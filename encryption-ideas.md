# Parquet Encryption Ideas

## 1. Native Parquet Encryption
- Use `pyarrow` native Parquet encryption support.
- Can encrypt:
  - footer only
  - selected columns
  - entire file
- Benefits:
  - preserves Parquet structure and schema metadata
  - can allow Parquet-aware readers to decrypt if they support it
- Tradeoffs:
  - not universally supported by all readers
  - increased implementation complexity and key management
- Implementation note:
  - use `pyarrow.parquet.write_table()` with `EncryptionProperties`

## 2. Post-write File Encryption
- Write the `.parquet` file normally, then encrypt the final file as a separate step.
- Tools/libraries:
  - `openssl enc -aes-256-gcm`
  - `gpg`
  - `age`
  - Python `cryptography`
- Benefits:
  - compatible with any Parquet reader after decryption
  - simpler to implement than native Parquet encryption
- Tradeoffs:
  - file becomes opaque until decrypted
  - not Parquet-aware, so no selective column decryption

## 3. Filesystem or Volume Encryption
- Encrypt the directory or disk where Parquet files are stored.
- Examples:
  - macOS FileVault
  - Linux LUKS
  - encrypted cloud storage volumes
- Benefits:
  - transparent to the collector code
  - no app-side encryption changes needed
- Tradeoffs:
  - protection only at the filesystem/volume layer
  - files are accessible while the volume is mounted

## 4. Cloud Storage Encryption
- Encrypt Parquet files when storing them in cloud object storage.
- Cloud provider options:
  - AWS S3 SSE-S3, SSE-KMS, client-side encryption
  - GCS CMEK/CSEK
  - Azure Storage encryption
- Benefits:
  - strong integration with cloud key management
  - works well for remote storage
- Tradeoffs:
  - not directly applicable to local file generation without cloud storage usage

## 5. Column-level Parquet Encryption
- Use Parquet native encryption to protect only sensitive columns.
- Benefits:
  - enables selective encryption of sensitive data while leaving other data readable
- Tradeoffs:
  - requires support for native Parquet encryption
  - more complex mapping between columns and keys

## Recommendation for This Project
- If compatibility is key, use post-write encryption with a standard library/tool.
- If you want Parquet-native protection and can control the reader, use `pyarrow` encryption.
- If you want zero code changes in the collector, use filesystem/volume encryption.
