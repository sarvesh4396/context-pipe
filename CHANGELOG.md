# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial release of context-pipe core package
- `Conversation`, `Message`, `Summary` data models
- `Role` and `WipeMode` enums for message classification and compaction strategy
- `AbstractBackend` interface for pluggable persistence
- `AbstractCompactor` interface for provider-agnostic summarization
- `WindowPolicy` for token budget management
- `CompactionEngine` for automatic context compaction
- `MemoryBackend` for in-process storage
- `RedisBackend` for Redis-backed persistence
- `SQLAlchemyBackend` for SQL database persistence
- Full async/await support throughout
- Comprehensive type hints with mypy strict mode compliance
- Initial documentation and getting started guide

[Unreleased]: https://github.com/sarvesh4396/context-pipe/compare/v0.1.0...HEAD
