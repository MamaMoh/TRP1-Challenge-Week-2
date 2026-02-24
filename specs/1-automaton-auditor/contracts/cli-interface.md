# CLI Interface Contract: Automaton Auditor

**Date**: 2026-02-24  
**Purpose**: Define the command-line interface contract for the Automaton Auditor tool

## Command Syntax

```bash
python main.py [OPTIONS] --repo <REPO_URL> --pdf <PDF_PATH>
```

## Arguments

### Required Arguments

- `--repo <REPO_URL>` or `-r <REPO_URL>`
  - **Type**: String (URL)
  - **Format**: Valid GitHub repository URL
  - **Example**: `https://github.com/user/repo.git`
  - **Validation**: Must start with `https://github.com/` or `git@github.com:`
  - **Error**: If invalid or unreachable, exit with code 1 and error message

- `--pdf <PDF_PATH>` or `-p <PDF_PATH>`
  - **Type**: String (file path)
  - **Format**: Absolute or relative path to PDF file
  - **Example**: `./reports/week2_report.pdf`
  - **Validation**: File must exist and be readable
  - **Error**: If file not found or unreadable, exit with code 1 and error message

### Optional Arguments

- `--output <OUTPUT_DIR>` or `-o <OUTPUT_DIR>`
  - **Type**: String (directory path)
  - **Format**: Absolute or relative path to output directory
  - **Default**: `audit/report_onself_generated/`
  - **Example**: `audit/report_onpeer_generated/`
  - **Validation**: Directory will be created if it doesn't exist
  - **Behavior**: Report saved as `audit_report.md` in specified directory

- `--rubric <RUBRIC_PATH>` or `-R <RUBRIC_PATH>`
  - **Type**: String (file path)
  - **Format**: Absolute or relative path to rubric JSON file
  - **Default**: `rubric/week2_rubric.json`
  - **Example**: `rubric/custom_rubric.json`
  - **Validation**: File must exist and be valid JSON matching rubric schema
  - **Error**: If invalid, exit with code 1 and error message

- `--verbose` or `-v`
  - **Type**: Flag (boolean)
  - **Default**: False
  - **Behavior**: Enable verbose logging to stdout
  - **Output**: Progress messages, evidence collection status, judge reasoning

- `--trace` or `-t`
  - **Type**: Flag (boolean)
  - **Default**: False (unless LANGCHAIN_TRACING_V2=true in .env)
  - **Behavior**: Enable LangSmith tracing (requires LANGCHAIN_API_KEY)
  - **Output**: Trace URL printed to stdout if enabled

- `--help` or `-h`
  - **Type**: Flag (boolean)
  - **Behavior**: Display help message and exit
  - **Output**: Usage information, argument descriptions, examples

## Environment Variables

The following environment variables are read from `.env` file (or environment):

- `OPENAI_API_KEY` (required)
  - **Purpose**: API key for OpenAI LLM operations
  - **Error**: If missing, exit with code 1 and error message

- `LANGCHAIN_TRACING_V2` (optional)
  - **Purpose**: Enable LangSmith tracing
  - **Values**: `true` or `false`
  - **Default**: `false`

- `LANGCHAIN_API_KEY` (optional, required if tracing enabled)
  - **Purpose**: API key for LangSmith tracing
  - **Error**: If tracing enabled but key missing, warning printed, tracing disabled

- `LANGCHAIN_PROJECT` (optional)
  - **Purpose**: Project name for LangSmith traces
  - **Default**: `automaton-auditor`

## Exit Codes

- `0`: Success - Audit completed, report generated
- `1`: Error - Invalid arguments, missing files, or execution failure
- `2`: Configuration error - Missing API keys or invalid configuration

## Output

### Standard Output (stdout)

- Progress messages (if `--verbose` enabled)
- Trace URL (if `--trace` enabled and tracing successful)
- Final report path (on success)

### Standard Error (stderr)

- Error messages
- Warning messages
- Debug information (if verbose)

### Files Generated

- `<OUTPUT_DIR>/audit_report.md`: Main audit report (Markdown format)
- `<OUTPUT_DIR>/langsmith_trace.json` (optional): Exported LangSmith trace if `--trace` enabled

## Examples

### Basic Usage

```bash
python main.py --repo https://github.com/user/week2-repo.git --pdf ./report.pdf
```

### Custom Output Directory

```bash
python main.py \
  --repo https://github.com/user/week2-repo.git \
  --pdf ./report.pdf \
  --output audit/report_onpeer_generated/
```

### Verbose Mode with Tracing

```bash
python main.py \
  --repo https://github.com/user/week2-repo.git \
  --pdf ./report.pdf \
  --verbose \
  --trace
```

### Custom Rubric

```bash
python main.py \
  --repo https://github.com/user/week2-repo.git \
  --pdf ./report.pdf \
  --rubric rubric/custom_rubric.json
```

## Error Messages

All error messages follow this format:

```
ERROR: [Component]: [Description]
```

Examples:
- `ERROR: Repository: Failed to clone https://github.com/invalid/repo.git`
- `ERROR: PDF: File not found: ./missing_report.pdf`
- `ERROR: Configuration: Missing OPENAI_API_KEY in environment`

## Success Message

On successful completion:

```
✓ Audit complete. Report saved to: audit/report_onself_generated/audit_report.md
[LangSmith Trace: https://smith.langchain.com/o/...] (if tracing enabled)
```

## Contract Guarantees

1. **Idempotency**: Running the same command twice produces identical reports (assuming inputs unchanged)
2. **Determinism**: Same inputs always produce same outputs (no randomness in synthesis)
3. **Error Handling**: All errors are caught and reported, no crashes
4. **Cleanup**: Temporary directories are cleaned up after execution
5. **Validation**: All inputs are validated before processing begins
