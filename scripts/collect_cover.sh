set -euo pipefail
IFS=$'\n\t'

# Fixed directories
tmpdir="$(pwd)"
PROFDIR="$tmpdir/collected_profiles"
EXEDIR="$tmpdir"
OUTDIR="$tmpdir/coverage_reports"
LLVM_PREFIX="/home/kd/workplace/xscc_release_test/llmv_bin/x86_llvm19_flang_fix_new/bin/"

# Ensure llvm-cov is available
LLVM_COV="${LLVM_PREFIX}llvm-cov"
command -v "$LLVM_COV" >/dev/null 2>&1 || {
  echo >&2 "Error: llvm-cov not found at '$LLVM_COV'."; exit 1;
}

# Create output directories
TEXTDIR="$OUTDIR/text"
HTMLDIR="$OUTDIR/html"
mkdir -p "$TEXTDIR" "$HTMLDIR"

echo "PROFDIR: $PROFDIR"
echo "EXEDIR:  $EXEDIR"
echo "OUTDIR:  $OUTDIR"

echo "Starting coverage collection..."

# Iterate over each .profdata file
for proffile in "$PROFDIR"/*.profdata; do
  bench_full=$(basename "$proffile" .profdata)
  # Extract benchmark name after first dot, e.g., '400.perlbench' -> 'perlbench'
  bench_name="${bench_full#*.}"
  echo "Processing benchmark: $bench_name"

  # Locate corresponding executable folder
  exe_folder="$EXEDIR/$bench_full"
  if [ ! -d "$exe_folder" ]; then
    echo "Warning: Executable directory '$exe_folder' does not exist, skipping."
    continue
  fi

  # Find executable matching '*_base.' pattern, ignore scripts
  exe_path=$(find "$exe_folder" -maxdepth 1 -type f -perm /u+x \
    -name "*_base.*" ! -name "*.py" ! -name "*.pl" | head -n 1)
    # -name "${bench_name}_base.*" ! -name "*.py" ! -name "*.pl" | head -n 1)
  if [ -z "$exe_path" ]; then
    echo "Warning: No suitable executable matching '${bench_name}_base.*' found in '$exe_folder', skipping."
    continue
  fi

  # Prepare output paths
  text_report="$TEXTDIR/${bench_name}.txt"
  html_out="$HTMLDIR/${bench_name}.html"

  # Generate summary-only text report
  echo "  Generating text report: $text_report"
  "$LLVM_COV" report \
    "$exe_path" \
    --format=text \
    -instr-profile="$proffile" \
    --summary-only \
    --show-region-summary \
    --show-branch-summary \
    > "$text_report"

  # Generate full HTML report
  echo "  Generating HTML report: $html_out"
  "$LLVM_COV" show \
    --format=html \
    --instr-profile="$proffile" \
    --show-line-counts-or-regions \
    --show-branches=count \
    --show-branch-summary \
    --show-region-summary \
    --show-instantiations \
    --show-mcdc-summary \
    --show-expansions \
    --object="$exe_path" \
    -o "$html_out"

  echo "  Done: $bench_name"
done

echo "All benchmarks processed. Reports available in $OUTDIR."
