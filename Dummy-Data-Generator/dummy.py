import os
import random
import argparse
from pathlib import Path
import time
from typing import List, Dict, Tuple

# -----------------------------------------
# Defaults & Config
# -----------------------------------------

DEFAULT_FILE_TYPES = [
    "txt", "log", "csv",
    "json", "xml",
    "png", "pdf",
    "zip",
]

# Default small file size ranges per type (bytes)
DEFAULT_SIZE_RANGES: Dict[str, Tuple[int, int]] = {
    "txt":  (4 * 1024, 64 * 1024),         # 4 KB - 64 KB
    "log":  (4 * 1024, 64 * 1024),
    "csv":  (4 * 1024, 64 * 1024),
    "json": (2 * 1024, 32 * 1024),
    "xml":  (2 * 1024, 32 * 1024),
    "png":  (32 * 1024, 256 * 1024),       # 32 KB - 256 KB
    "pdf":  (32 * 1024, 256 * 1024),
    "zip":  (64 * 1024, 512 * 1024),       # 64 KB - 512 KB
}

GLOBAL_MIN_FILE_SIZE = 2 * 1024  # 2 KB

# -----------------------------------------
# Core helpers
# -----------------------------------------

def write_random_binary(path: Path, size_bytes: int, dry_run: bool = False):
    """
    For small files it's fine to just allocate once and write once.
    """
    if dry_run:
        return
    with path.open("wb") as f:
        f.write(os.urandom(size_bytes))


def create_dummy_file(
    base_dir: Path,
    index: int,
    file_type: str,
    size_bytes: int,
    dry_run: bool = False
) -> int:
    """
    Create one dummy file in base_dir and return its "actual" size in bytes.
    In dry_run mode, no file is written but the size is returned as if it was.
    """
    base_dir.mkdir(parents=True, exist_ok=True)

    filename = f"file_{index:06d}.{file_type}"
    path = base_dir / filename

    write_random_binary(path, size_bytes, dry_run=dry_run)

    # In dry-run, pretend the size is exactly what we requested
    if dry_run:
        return size_bytes

    return path.stat().st_size


def choose_file_type(index: int, file_types: List[str]) -> str:
    """
    Deterministic rotation through the given file_types.
    """
    return file_types[index % len(file_types)]


def build_size_ranges(
    enabled_types: List[str],
    min_size_kb: int = None,
    max_size_kb: int = None
) -> Dict[str, Tuple[int, int]]:
    """
    Build the size range table for the currently enabled extensions.
    Optionally override global min/max for all types.
    """
    ranges = {}
    for ext in enabled_types:
        if ext in DEFAULT_SIZE_RANGES:
            base_min, base_max = DEFAULT_SIZE_RANGES[ext]
        else:
            # Fallback range
            base_min, base_max = (4 * 1024, 64 * 1024)

        if min_size_kb is not None:
            base_min = max(base_min, min_size_kb * 1024)
        if max_size_kb is not None:
            base_max = min(base_max, max_size_kb * 1024)
        if base_max < base_min:
            base_max = base_min

        ranges[ext] = (base_min, base_max)
    return ranges


def interactive_target_mb_menu() -> int:
    """
    Ask the user interactively for target dataset size.
    """
    print("Select data size to generate:")
    print("  1) 100 MB")
    print("  2) 500 MB")
    print("  3) 1 GB  (1024 MB)")
    print("  4) 2 GB  (2048 MB)")
    print("  5) Custom size (MB)")
    choice = input("Enter choice (1-5): ").strip()

    if choice == "1":
        return 100
    elif choice == "2":
        return 500
    elif choice == "3":
        return 1024
    elif choice == "4":
        return 2048
    elif choice == "5":
        while True:
            val = input("Enter custom size in MB: ").strip()
            try:
                mb = int(val)
                if mb > 0:
                    return mb
                print("Please enter a positive integer.")
            except ValueError:
                print("Invalid number, try again.")
    else:
        print("Invalid choice, defaulting to 1 GB (1024 MB).")
        return 1024


def estimate_sizes_for_approx_files(
    target_mb: int,
    approx_files: int
) -> Tuple[int, int]:
    """
    Given total MB and desired number of files, estimate reasonable
    min/max sizes (in bytes) around the average.
    """
    total_bytes = target_mb * 1024 * 1024
    avg = total_bytes // max(1, approx_files)

    # e.g. 50% around average
    min_sz = max(GLOBAL_MIN_FILE_SIZE, int(avg * 0.5))
    max_sz = max(min_sz, int(avg * 1.5))

    return min_sz, max_sz


# -----------------------------------------
# Generator
# -----------------------------------------

def generate_dummy_data(
    output_dir: Path,
    target_mb: int,
    file_types: List[str],
    size_ranges: Dict[str, Tuple[int, int]],
    dry_run: bool = False,
) -> None:
    """
    Generate dummy data up to approximately target_mb MB
    in a single folder, with many small files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    target_bytes = target_mb * 1024 * 1024

    total_bytes = 0
    file_index = 0
    start_time = time.time()
    last_printed_percent = -5  # to force initial print
    per_ext_count = {ext: 0 for ext in file_types}

    print(f"Target size: ~{target_mb} MB ({target_bytes:,} bytes)")
    print(f"Output directory: {output_dir.resolve()}")
    if dry_run:
        print("Mode: DRY RUN (no files will actually be created).")
    print()

    while total_bytes < target_bytes:
        file_index += 1
        remaining = target_bytes - total_bytes

        if remaining <= GLOBAL_MIN_FILE_SIZE:
            size_bytes = remaining
            file_type = choose_file_type(file_index, file_types)
        else:
            file_type = choose_file_type(file_index, file_types)
            min_sz, max_sz = size_ranges.get(
                file_type,
                (GLOBAL_MIN_FILE_SIZE, 64 * 1024)
            )
            max_sz = min(max_sz, remaining)
            if max_sz < min_sz:
                size_bytes = max(min_sz, remaining)
            else:
                size_bytes = random.randint(min_sz, max_sz)

        actual_size = create_dummy_file(
            output_dir,
            file_index,
            file_type,
            size_bytes,
            dry_run=dry_run
        )
        total_bytes += actual_size
        per_ext_count[file_type] += 1

        percent = int((total_bytes / target_bytes) * 100)
        # Print only every 5% to reduce slowdown
        if percent - last_printed_percent >= 5:
            last_printed_percent = percent
            total_mb = total_bytes / (1024 * 1024)
            print(
                f"[{percent:3d}%] Files: {file_index:6d} "
                f"| Total: {total_mb:8.2f} MB",
                end="\r"
            )

    elapsed = time.time() - start_time
    print("\n\nDone!")
    print(f"Created {file_index} files (or would create, in dry-run).")
    print(f"Total size: {total_bytes / (1024 * 1024):.2f} MB")
    print(
        f"Time taken: {elapsed:.2f} seconds "
        f"(~{(total_bytes / (1024 * 1024)) / max(elapsed, 0.001):.2f} MB/s)"
    )

    print("\nFile count by extension:")
    for ext, count in per_ext_count.items():
        print(f"  .{ext}: {count} files")


# -----------------------------------------
# CLI parsing
# -----------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Advanced dummy data generator (many small files, single folder)."
    )

    parser.add_argument(
        "--out",
        type=str,
        default="dummy_data_output",
        help="Output folder (default: ./dummy_data_output)",
    )
    parser.add_argument(
        "--target-mb",
        type=int,
        default=None,
        help="Total size in MB. If omitted and --no-interactive is not set, an interactive menu is shown.",
    )
    parser.add_argument(
        "--approx-files",
        type=int,
        default=None,
        help="Approximate number of files to create. "
             "This will auto-tune file size range around target_mb / approx_files.",
    )
    parser.add_argument(
        "--ext",
        type=str,
        default=None,
        help="Comma-separated list of extensions to use, e.g. 'txt,pdf,png'. "
             "Defaults to all supported types.",
    )
    parser.add_argument(
        "--min-size-kb",
        type=int,
        default=None,
        help="Override minimum file size (KB) for all types.",
    )
    parser.add_argument(
        "--max-size-kb",
        type=int,
        default=None,
        help="Override maximum file size (KB) for all types.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan and print stats but do not actually create any files.",
    )
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Disable interactive prompts. You must provide --target-mb.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible runs.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # Seed random if requested
    if args.seed is not None:
        random.seed(args.seed)

    # Resolve output directory
    output_dir = Path(args.out)

    # Determine target_mb
    if args.target_mb is not None:
        target_mb = args.target_mb
        if target_mb <= 0:
            raise SystemExit("Error: --target-mb must be a positive integer.")
    else:
        if args.no_interactive:
            raise SystemExit(
                "Error: --target-mb is required when --no-interactive is set."
            )
        target_mb = interactive_target_mb_menu()

    # Determine enabled file types
    if args.ext:
        requested_exts = [e.strip().lower().lstrip(".") for e in args.ext.split(",")]
        enabled_types = [e for e in requested_exts if e in DEFAULT_FILE_TYPES]
        unknown = [e for e in requested_exts if e not in DEFAULT_FILE_TYPES]
        if unknown:
            print(f"Warning: unsupported extensions ignored: {', '.join(unknown)}")
        if not enabled_types:
            raise SystemExit("Error: after filtering, no valid extensions remain.")
    else:
        enabled_types = list(DEFAULT_FILE_TYPES)

    # Build size ranges
    size_ranges = build_size_ranges(
        enabled_types,
        min_size_kb=args.min_size_kb,
        max_size_kb=args.max_size_kb,
    )

    # If approx-files provided, auto-tune a global min/max and override ranges
    if args.approx_files is not None:
        if args.approx_files <= 0:
            raise SystemExit("Error: --approx-files must be a positive integer.")
        est_min, est_max = estimate_sizes_for_approx_files(target_mb, args.approx_files)
        print(
            f"Auto-tuning size ranges for ~{args.approx_files} files: "
            f"min ≈ {est_min // 1024} KB, max ≈ {est_max // 1024} KB"
        )
        size_ranges = {
            ext: (est_min, est_max)
            for ext in enabled_types
        }

    # Summary of configuration
    print("Configuration:")
    print(f"  Output directory : {output_dir}")
    print(f"  Target size      : {target_mb} MB")
    print(f"  Extensions       : {', '.join(enabled_types)}")
    if args.approx_files:
        print(f"  Approx. files    : {args.approx_files}")
    if args.min_size_kb:
        print(f"  Min size (KB)    : {args.min_size_kb}")
    if args.max_size_kb:
        print(f"  Max size (KB)    : {args.max_size_kb}")
    if args.seed is not None:
        print(f"  Random seed      : {args.seed}")
    print(f"  Dry run          : {args.dry_run}")
    print()

    generate_dummy_data(
        output_dir=output_dir,
        target_mb=target_mb,
        file_types=enabled_types,
        size_ranges=size_ranges,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
