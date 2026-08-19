"""Execute all notebooks in notebooks/ and save outputs in-place using in-process IPython."""
import io
import os
import sys
from pathlib import Path
import nbformat
from IPython.core.interactiveshell import InteractiveShell

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS_DIR = ROOT / "notebooks"
sys.path.insert(0, str(NOTEBOOKS_DIR))
sys.path.insert(0, str(ROOT))

notebook_files = [
    "01_embeddings_index.ipynb",
    "02_hybrid_search_rrf.ipynb",
    "03_search_api_benchmark.ipynb",
    "04_feast_feature_store.ipynb",
    "05_filtered_search.ipynb",
    "06_agent_retrieval.ipynb",
    "07_semantic_cache.ipynb",
    "08_feature_engineering.ipynb",
]


def run_notebook(nb_name: str):
    nb_path = NOTEBOOKS_DIR / nb_name
    print(f"Executing {nb_name} ...", flush=True)
    with nb_path.open("r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    orig_cwd = os.getcwd()
    os.chdir(str(NOTEBOOKS_DIR))

    shell = InteractiveShell()
    shell.reset()

    execution_count = 1
    for cell in nb.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            code = cell.source
            if not code.strip():
                continue

            stdout_buf = io.StringIO()
            stderr_buf = io.StringIO()

            orig_stdout = sys.stdout
            orig_stderr = sys.stderr
            sys.stdout = stdout_buf
            sys.stderr = stderr_buf

            try:
                res = shell.run_cell(code, store_history=True)
            finally:
                sys.stdout = orig_stdout
                sys.stderr = orig_stderr

            stdout_text = stdout_buf.getvalue()
            stderr_text = stderr_buf.getvalue()

            if stdout_text:
                cell.outputs.append(nbformat.v4.new_output(
                    output_type="stream",
                    name="stdout",
                    text=stdout_text
                ))
            if stderr_text:
                cell.outputs.append(nbformat.v4.new_output(
                    output_type="stream",
                    name="stderr",
                    text=stderr_text
                ))

            if res.error_in_exec:
                err = res.error_in_exec
                cell.outputs.append(nbformat.v4.new_output(
                    output_type="error",
                    ename=type(err).__name__,
                    evalue=str(err),
                    traceback=[f"{type(err).__name__}: {err}"]
                ))
                os.chdir(orig_cwd)
                raise err

            if res.result is not None:
                cell.outputs.append(nbformat.v4.new_output(
                    output_type="execute_result",
                    execution_count=execution_count,
                    data={"text/plain": repr(res.result)}
                ))

            cell.execution_count = execution_count
            execution_count += 1

    os.chdir(orig_cwd)
    with nb_path.open("w", encoding="utf-8") as f:
        nbformat.write(nb, f)
    print(f"  -> PASS {nb_name}", flush=True)


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else notebook_files
    for nb_name in targets:
        try:
            run_notebook(nb_name)
        except Exception as e:
            print(f"  -> FAILED {nb_name}: {e}", flush=True)
            raise


if __name__ == "__main__":
    main()
