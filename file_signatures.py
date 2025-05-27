FILE_SIGNATURES = {
    "jpg": {
        "start_sig": [b'\xff\xd8\xff\xe0', b'\xff\xd8\xff\xe1'],
        "end_sig": b'\xff\xd9'
    },
    "png": {
        "start_sig": b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a', # \x89PNG\r\n\x1a\n
        "end_sig": b'\x49\x45\x4e\x44\xae\x42\x60\x82'    # IEND®B`‚
    },
    "pdf": {
        "start_sig": b'\x25\x50\x44\x46', # %PDF
    },
    "docx": {
        "start_sig": b'\x50\x4b\x03\x04', # PK\x03\x04
    }
}

if __name__ == '__main__':
    # Example usage:
    print("JPG Start Signatures:", [sig.hex().upper() for sig in FILE_SIGNATURES["jpg"]["start_sig"]])
    print("JPG End Signature:", FILE_SIGNATURES["jpg"]["end_sig"].hex().upper())

    print("PNG Start Signature:", FILE_SIGNATURES["png"]["start_sig"].hex().upper())
    print("PNG End Signature:", FILE_SIGNATURES["png"]["end_sig"].hex().upper())

    print("PDF Start Signature:", FILE_SIGNATURES["pdf"]["start_sig"].hex().upper())
    # print("PDF End Signature:", FILE_SIGNATURES["pdf"]["end_sig"]) # This would cause an error as it's not defined

    print("DOCX Start Signature:", FILE_SIGNATURES["docx"]["start_sig"].hex().upper())

    # How to check if an end signature exists
    if FILE_SIGNATURES["pdf"].get("end_sig"):
        print("PDF End Signature:", FILE_SIGNATURES["pdf"]["end_sig"].hex().upper())
    else:
        print("PDF End Signature: Not defined")

    if FILE_SIGNATURES["docx"].get("end_sig"):
        print("DOCX End Signature:", FILE_SIGNATURES["docx"]["end_sig"].hex().upper())
    else:
        print("DOCX End Signature: Not defined")
