# WhisperForge Changelog

All notable changes to WhisperForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2024-03-20

### Added
- Automatic audio file chunking for files over 25MB
- Detailed progress logging in transcription service
- Extended timeout handling for large files

### Changed
- Reduced chunk size to 10MB for faster processing
- Transcription service timeout increased to 300s
- Frontend request timeout increased to 300s
- Improved error handling and logging
- Added bitrate compression for audio chunks

### Fixed
- Timeout issues with larger audio files
- Memory handling for large file processing
- Temporary file cleanup reliability

### Technical Details
- Chunk size: 10MB with 128k bitrate compression
- Max file size remains at 200MB
- Added progress tracking per chunk
- Enhanced error logging across services
- Improved temp file management

### Known Issues
- Limited progress feedback in frontend during chunking
- No automatic retry on chunk failure
- Processing time increases linearly with file size

## [0.1.0] - 2024-11-18

### Added
- Initial release
- Audio file upload and transcription
- Notion integration
- Insights extraction
- Language detection
- Chunking support for large files

### Fixed
- Notion emoji validation issue
- Audio processing compatibility with Python 3.11

## [Unreleased] - 2024-11-18
### Added
- Monitoring infrastructure with Prometheus and Grafana
- Basic Notion integration in storage service
- Health check endpoints across all services

### Changed
- Updated project structure with monitoring directory
- Enhanced error handling in storage service