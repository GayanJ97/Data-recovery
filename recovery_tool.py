import os
import sys # For potentially more detailed error messages if needed

# Attempt to import FILE_SIGNATURES early for functions that might use it as a default
try:
    from file_signatures import FILE_SIGNATURES
except ImportError:
    # This is a fallback. The main execution block will handle the error more gracefully
    # if the import fails there, preventing the script from running.
    # Defining it as None or {} allows function definitions to proceed without NameError.
    print("Initial attempt: file_signatures.py not found or FILE_SIGNATURES not defined.", file=sys.stderr)
    FILE_SIGNATURES = {} 

DEFAULT_RECOVERY_SIZES = {
    "pdf": 2 * 1024 * 1024,  # 2MB
    "docx": 5 * 1024 * 1024, # 5MB
    "default_min": 512 * 1024 # 512KB default for types without end_sig and not in this list
}

def get_max_signature_length(signatures):
    """
    Calculates the maximum length of any start or end signature.
    This is used to determine the size of the overlap buffer between chunks.
    """
    max_len = 0
    if not signatures:
        return 16 # Default if no signatures loaded, to have some overlap

    for sig_data in signatures.values():
        # Check start signatures
        start_s = sig_data.get("start_sig")
        if isinstance(start_s, list):
            for s_sig in start_s:
                if isinstance(s_sig, bytes):
                    max_len = max(max_len, len(s_sig))
        elif isinstance(start_s, bytes):
            max_len = max(max_len, len(start_s))
        
        # Check end signature
        end_s = sig_data.get("end_sig")
        if isinstance(end_s, bytes):
            max_len = max(max_len, len(end_s))
            
    return max_len if max_len > 0 else 16 # Ensure at least a small buffer

def recover_files(partition_path, recovery_folder, signatures):
    """
    Recovers files from a raw partition based on file signatures.
    """
    if not signatures:
        print("Error: No file signatures loaded. Cannot proceed with recovery.", file=sys.stderr)
        return

    try:
        os.makedirs(recovery_folder, exist_ok=True)
        print(f"Recovery folder '{recovery_folder}' ensured/created.")
    except OSError as e:
        print(f"Error creating recovery folder '{recovery_folder}': {e}", file=sys.stderr)
        return

    partition_file = None  # Initialize to ensure it's defined for finally block
    try:
        partition_file = open(partition_path, 'rb')
        print(f"Successfully opened partition '{partition_path}'.")
    except PermissionError as e:
        print(f"Permission denied for partition '{partition_path}': {e}. Try running as administrator or with sudo.", file=sys.stderr)
        return
    except IOError as e:
        print(f"Error opening partition '{partition_path}': {e}. Check path and permissions.", file=sys.stderr)
        return

    file_count = 0
    chunk_size = 4 * 1024 * 1024  # 4MB chunks
    current_offset = 0
    previous_overlap = b''
    # max_sig_len must be at least 1 for slicing chunk[-(max_sig_len - 1):] to work without error if max_sig_len is 0
    max_sig_len = max(1, get_max_signature_length(signatures)) 
    
    print(f"Starting recovery scan. Chunk size: {chunk_size // (1024*1024)}MB, Max signature length for overlap: {max_sig_len} bytes.")

    try:
        while True:
            try:
                partition_file.seek(current_offset)
                chunk = partition_file.read(chunk_size)
            except IOError as e:
                print(f"Error reading from partition at offset {current_offset}: {e}", file=sys.stderr)
                break # Stop if we can't read

            if not chunk:
                print("End of partition reached.")
                break

            search_buffer = previous_overlap + chunk
            # This offset tracks where the next search for ANY signature should begin within the current search_buffer
            # It's advanced after a file is processed (or a start_sig is processed without full recovery)
            # to avoid re-processing the same data within this search_buffer iteration.
            processed_up_to_in_buffer = 0

            while processed_up_to_in_buffer < len(search_buffer):
                found_this_iteration = False
                earliest_found_start_offset_in_partition = float('inf')
                
                # Iterate through all signatures to find the one that appears earliest
                # This basic approach doesn't fully solve overlapping signatures but is a start
                # A more robust method might involve a more complex state machine or Aho-Corasick.
                
                # The following loop finds the *next* available signature in the remainder of the buffer.
                # This is still not perfect for truly overlapping different file types but tries to process sequentially.
                
                next_file_abs_start_offset = -1
                next_file_details = {} # Store details of the file to process

                current_search_point_in_buffer = processed_up_to_in_buffer
                
                for file_ext, sig_data in signatures.items():
                    start_sigs_list = sig_data.get("start_sig", [])
                    if not isinstance(start_sigs_list, list):
                        start_sigs_list = [start_sigs_list]

                    for start_sig in start_sigs_list:
                        if not start_sig: continue

                        found_idx_in_buffer = search_buffer.find(start_sig, current_search_point_in_buffer)
                        
                        if found_idx_in_buffer != -1:
                            abs_start_offset_in_partition = current_offset - len(previous_overlap) + found_idx_in_buffer
                            if next_file_abs_start_offset == -1 or abs_start_offset_in_partition < next_file_abs_start_offset:
                                next_file_abs_start_offset = abs_start_offset_in_partition
                                next_file_details = {
                                    "ext": file_ext,
                                    "sig_data": sig_data,
                                    "start_sig": start_sig,
                                    "found_idx_in_buffer": found_idx_in_buffer,
                                    "abs_offset": abs_start_offset_in_partition
                                }
                
                if not next_file_details: # No more signatures found in the rest of the buffer
                    break # Exit the inner while loop, advance to next chunk

                # Process the earliest found signature
                file_ext = next_file_details["ext"]
                sig_data = next_file_details["sig_data"]
                start_sig = next_file_details["start_sig"]
                found_idx_in_buffer = next_file_details["found_idx_in_buffer"]
                abs_start_offset_in_partition = next_file_details["abs_offset"]

                file_count += 1
                output_filename = os.path.join(recovery_folder, f"recovered_{file_count:04d}.{file_ext}")
                print(f"\nFound potential {file_ext.upper()} at offset {abs_start_offset_in_partition} (0x{abs_start_offset_in_partition:X})")

                file_data = None
                end_sig = sig_data.get("end_sig")
                advance_buffer_by = len(start_sig) # Default advance if no data recovered

                if end_sig:
                    search_for_end_sig_from = found_idx_in_buffer + len(start_sig)
                    found_end_idx_in_buffer = search_buffer.find(end_sig, search_for_end_sig_from)

                    if found_end_idx_in_buffer != -1:
                        actual_end_data_offset_in_buffer = found_end_idx_in_buffer + len(end_sig)
                        file_data = search_buffer[found_idx_in_buffer : actual_end_data_offset_in_buffer]
                        print(f"  End signature found within current search buffer. File length: {len(file_data)} bytes.")
                        advance_buffer_by = actual_end_data_offset_in_buffer - found_idx_in_buffer
                    else:
                        print(f"  Start signature for {file_ext.upper()} found, but end signature not within current search buffer (approx {len(search_buffer)/(1024*1024):.2f}MB).")
                        print(f"  File at {output_filename} will not be saved as end signature was not immediately found.")
                        file_data = None # Ensure not saved
                        # advance_buffer_by remains len(start_sig) to skip this start_sig
                else: # No end_sig defined
                    size_to_recover = DEFAULT_RECOVERY_SIZES.get(file_ext, DEFAULT_RECOVERY_SIZES["default_min"])
                    print(f"  No end signature. Attempting fixed-size recovery of {size_to_recover // 1024}KB.")
                    
                    # Read directly from partition for fixed-size recovery
                    # This ensures we get the data even if it spans beyond current chunk,
                    # but is less efficient than if we could use search_buffer.
                    # For simplicity, we'll use search_buffer if the data is fully contained.
                    if found_idx_in_buffer + size_to_recover <= len(search_buffer):
                        file_data = search_buffer[found_idx_in_buffer : found_idx_in_buffer + size_to_recover]
                        print(f"  Extracted {len(file_data)} bytes (fixed-size) from search buffer.")
                        advance_buffer_by = size_to_recover
                    else:
                        # If not fully in buffer, read from disk (more accurate but slower)
                        # This part is complex due to managing partition_file's seek position
                        # relative to the main loop's current_offset.
                        print(f"  Fixed size recovery ({size_to_recover // 1024}KB) may extend beyond current buffer. Reading directly from partition.")
                        saved_pos = partition_file.tell()
                        try:
                            partition_file.seek(abs_start_offset_in_partition)
                            file_data = partition_file.read(size_to_recover)
                            print(f"  Extracted {len(file_data)} bytes (fixed-size) directly from partition.")
                        except Exception as e_read:
                            print(f"  Error during fixed-size direct read: {e_read}", file=sys.stderr)
                            file_data = None
                        finally:
                            partition_file.seek(saved_pos) # Restore for main loop reading
                        # advance_buffer_by remains len(start_sig) as this read was outside buffer flow
                        # This means the main current_offset will handle moving past this area.
                        # This is a simplification; ideally, buffer processing and main offset are tightly coupled.
                        advance_buffer_by = len(start_sig) # Minimal advance in buffer; main offset does the work.


                if file_data:
                    is_valid_recovery = False
                    if end_sig: # File with known end signature
                        if len(file_data) > len(start_sig) + len(end_sig):
                            is_valid_recovery = True
                    else: # File with fixed size recovery
                        if len(file_data) == size_to_recover: # Fixed size should be exact or it's partial
                             is_valid_recovery = True
                        elif len(file_data) > len(start_sig): # Or at least more than sig if read was short
                             print(f"  Warning: Recovered data ({len(file_data)}) for fixed-size is less than target ({size_to_recover}).")
                             is_valid_recovery = True


                    if is_valid_recovery:
                        try:
                            with open(output_filename, 'wb') as out_file:
                                out_file.write(file_data)
                            print(f"  Successfully saved: {output_filename} ({len(file_data)} bytes)")
                        except IOError as e:
                            print(f"  Error writing file {output_filename}: {e}", file=sys.stderr)
                            file_count -=1 # Decrement if save failed
                    else:
                        print(f"  Skipping save for {output_filename}, data recovered is too small or inconsistent ({len(file_data)} bytes).")
                        file_count -=1 # Decrement if save is skipped
                else: # file_data is None (e.g. end_sig not found)
                    file_count -=1 # Not a successful recovery, decrement counter

                processed_up_to_in_buffer = found_idx_in_buffer + advance_buffer_by
                found_this_iteration = True # To prevent breaking outer while loop if nothing found in one pass

            # Prepare overlap for the next chunk
            if max_sig_len > 1: # max_sig_len-1 could be 0 if max_sig_len is 1
                previous_overlap = chunk[-(max_sig_len - 1):]
            else: # No overlap if max_sig_len is 0 or 1 (e.g. single byte signatures only)
                previous_overlap = b''
            
            current_offset += chunk_size

    except MemoryError:
        print("Critical: MemoryError occurred. Not enough memory to load chunk or buffer. Try reducing chunk_size or closing other applications.", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected critical error occurred during the recovery process: {e} (Current offset: {current_offset})", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        if partition_file and not partition_file.closed:
            partition_file.close()
            print("Partition file closed.")
        print(f"\nRecovery attempt finished. Attempted to process {file_count} potential files.")


def get_target_partition():
    """
    Prints instructions for identifying the target partition and prompts the user for its path.
    """
    print("How to identify your target partition path:")
    print("-------------------------------------------")
    print("Windows:")
    print("  Open File Explorer, go to 'This PC'. The partitions are listed (e.g., C:, D:).")
    print("  For raw access, the path might be \\\\.\\PhysicalDriveN (e.g., \\\\.\\PhysicalDrive0, \\\\.\\PhysicalDrive1)")
    print("  - be very careful with this, as it represents the entire disk, not just a partition.")
    print("  For partitions, it's usually like \\\\.\\C:, \\\\.\\D: but accessing these directly for raw reads might be restricted.")
    print("  It might be more practical to ask for a drive letter like 'D:' and the script will try to open \\\\.\\D:.")
    print("-------------------------------------------")
    print("Linux:")
    print("  Open a terminal and run `lsblk` or `sudo fdisk -l` to list partitions (e.g., /dev/sda1, /dev/sdb2).")
    print("-------------------------------------------")
    print("macOS:")
    print("  Open Terminal and run `diskutil list` to list partitions (e.g., /dev/disk1s2).")
    print("-------------------------------------------")
    print("\nWARNING: Ensure you select the correct partition. Reading from the wrong partition can be harmless,")
    print("but if this script were to write (which it won't in recovery mode), it could cause data loss.")
    print("Double-check your selection.")
    print("-------------------------------------------")
    
    partition_path = input("Enter the full path to the target partition (e.g., D: on Windows, /dev/sda1 on Linux, /dev/disk2s1 on macOS): ")
    return partition_path.strip()

def get_recovery_folder():
    """
    Prompts the user for the path to a folder where recovered files will be saved.
    """
    print("\nIMPORTANT: Ensure this folder is on a different physical drive than the one you are recovering from")
    print("to avoid overwriting data.")
    print("-------------------------------------------")
    
    recovery_path = input("Enter the path to a folder on a DIFFERENT drive where recovered files will be saved: ")
    return recovery_path.strip()

if __name__ == '__main__':
    print("Starting Data Recovery Tool Setup...")
    
    # Attempt to import FILE_SIGNATURES here again, as it's critical for operation
    try:
        from file_signatures import FILE_SIGNATURES as imported_signatures
        if not imported_signatures: # Check if the imported dict is empty
             print("ERROR: FILE_SIGNATURES was imported but is empty. Check file_signatures.py.", file=sys.stderr)
             sys.exit(1)
    except ImportError:
        print("ERROR: Could not import FILE_SIGNATURES. Make sure file_signatures.py is in the same directory and is correctly formatted.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during import of FILE_SIGNATURES: {e}", file=sys.stderr)
        sys.exit(1)

    target_partition = get_target_partition()
    print(f"\nSelected target partition: '{target_partition}'")
    
    recovery_folder = get_recovery_folder()
    print(f"\nSelected recovery folder: '{recovery_folder}'")
    
    print("\nSetup Complete. Paths recorded.")
    print("Starting recovery process...")
    recover_files(target_partition, recovery_folder, imported_signatures)
