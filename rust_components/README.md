# Chariot Engine Rust Components

This directory contains high-performance Rust implementations of core Chariot Engine components.

## Components

### Graph Matching
- Implementation of trade loop finding algorithms
- Efficient graph operations for trade matching
- Python bindings via PyO3

### Trade Validation
- Fast trade validation system
- Type-safe validation rules
- Integration with Python codebase

## Building

```bash
# Build the library
cargo build --release

# Run tests
cargo test

# Build Python bindings
cargo build --release --features python
```

## Integration

These components can be integrated with the main Python codebase in several ways:
1. As a Python extension module (recommended)
2. As a standalone binary with JSON interface
3. As a microservice with REST API

See the examples directory for usage demonstrations. 