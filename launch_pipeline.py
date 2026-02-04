from src.pipeline import run_all

def run_pipeline():
    """Run the full Pixal pipeline.
    
    This function delegates to src.pipeline.run_all() which is the single
    source of truth for pipeline orchestration.
    """
    return run_all()

if __name__ == "__main__":
    run_pipeline()
