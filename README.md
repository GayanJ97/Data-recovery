# Python Data Recovery Script

## Description
This script attempts to recover files from a storage device (like a formatted hard drive or USB stick) by searching for known file signatures (magic numbers). It reads the raw device data and tries to carve out files based on these signatures.

## Prerequisites
- Python 3.x installed.
- The `file_signatures.py` file (containing the file signatures to search for) must be in the same directory as `recovery_tool.py`.

## How to Run

### Using `run_recovery.bat` on Windows (Recommended)
1.  **Ensure Prerequisites:**
    *   Python 3.x installed and added to your system's PATH.
    *   The `file_signatures.py` and `recovery_tool.py` files must be in the same directory as `run_recovery.bat`.
2.  **Identify your target partition:** For Windows, you need to specify the raw device path. For example, if your target partition is `D:`, you should use `\\.\D:` when the script prompts you. (See more details under "Manual Execution" step 1 if needed).
3.  **Prepare a recovery drive:** Ensure you have a separate physical storage device (another hard drive, a large USB stick) with enough free space. **DO NOT use a folder on the same drive you are recovering from.**
4.  **Run the Batch File:**
    *   Navigate to the directory containing `run_recovery.bat`.
    *   Right-click on `run_recovery.bat` and select **"Run as administrator"**.
    *   The script will then prompt you for the target partition and recovery folder.

### Manual Execution (All Platforms)
1.  **Identify your target partition:**
    *   **Windows:** Open File Explorer, go to 'This PC'. Partitions are listed (e.g., `C:`, `D:`). For the recovery script to get raw access, you must use a special path format when prompted:
        *   For a partition like `D:`, enter `\\.\D:`
        *   For a partition like `E:`, enter `\\.\E:`
        *   This `\\.\X:` notation is crucial for direct disk access.
        *   Paths like `\\.\PhysicalDriveN` (e.g., `\\.\PhysicalDrive0`) refer to entire physical disks, not just partitions. Accessing a whole disk this way is possible but **requires extreme caution** to ensure you are targeting the correct device, as it gives access to all partitions on that disk. For recovering a specific partition (like `D:`), using `\\.\D:` is generally safer.
    *   **Linux:** Open a terminal, run `lsblk` or `sudo fdisk -l` (e.g., `/dev/sda1`).
    *   **macOS:** Open Terminal, run `diskutil list` (e.g., `/dev/disk2s1`).
2.  **Prepare a recovery drive:** (This step is somewhat duplicated but good to have here too) Ensure you have a separate physical storage device (another hard drive, a large USB stick) with enough free space to save recovered files. **DO NOT use a folder on the same drive you are recovering from.**
3.  **Open a terminal or command prompt:**
    *   **Windows:** Search for `cmd` or `PowerShell`. **Run as Administrator.** (Required if not using the batch file)
    *   **Linux/macOS:** Open your terminal application.
4.  **Navigate to the script directory:** Use the `cd` command to go to the folder where you saved `recovery_tool.py` and `file_signatures.py`.
    ```bash
    cd path/to/your/script_directory
    ```
5.  **Run the script:**
    *   **Windows (as Administrator, if not using batch file):**
        ```bash
        python recovery_tool.py
        ```
    *   **Linux/macOS (with sudo for raw disk access):**
        ```bash
        sudo python3 recovery_tool.py
        ```
    The script will then prompt you to enter the target partition path and the recovery folder path.

## !!! CRUCIAL WARNINGS !!!
- **RUN WITH ADMINISTRATIVE/ROOT PRIVILEGES:** The script needs low-level access to read from a partition/drive.
  - For Windows, this means running Command Prompt/PowerShell "as Administrator" or using the `run_recovery.bat` file (which should also be run as administrator).
  - On Linux/macOS, use `sudo` when running the script (e.g., `sudo python3 recovery_tool.py`).
- **SELECT THE CORRECT PARTITION:** Double-check the partition path you provide. Reading from a system drive or the wrong drive could be problematic if mistakes are made, though this script is designed for read-only access to the source partition. The primary risk is choosing the wrong *recovery location* and overwriting data.
- **SAVE TO A DIFFERENT DRIVE:** Always save recovered files to a completely separate physical drive. Writing recovered files to the same drive you are recovering from will likely overwrite the very data you are trying to recover, leading to permanent data loss.
- **NO GUARANTEES:** Data recovery is complex. This script is a best-effort tool and provides NO GUARANTEE that it will recover any or all of your lost files. Success depends on many factors, including how the drive was formatted, whether data has been overwritten, file fragmentation, and the types of files.
- **RISK OF DATA LOSS (IF MISUSED):** While this script is designed to be read-only from the source partition, any data recovery attempt carries inherent risks if instructions are not followed precisely (especially regarding the recovery drive). Proceed with caution.
- **BACKUPS ARE KEY:** This incident highlights the importance of regular data backups.

## Customizing File Signatures
You can add or modify file signatures by editing the `FILE_SIGNATURES` dictionary in the `file_signatures.py` file. Each entry defines a file type (extension), its start signature(s), and optionally an end signature. Signatures are represented as byte strings.

## Disclaimer
This script is provided "as-is" without warranty of any kind. The authors or distributors are not responsible for any data loss or damage that may occur from its use. Use at your own risk.
