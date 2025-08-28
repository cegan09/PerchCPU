# Minimal Perch v2 CPU scorer + simple benchmark
# Usage:
#   python perch2_min.py /path/to/clips             -> writes perch_results.csv + perch_results_stats.txt
#   python perch2_min.py /path/to/clips my_output   -> writes my_output.csv + my_output_stats.txt

import sys, time, csv
from pathlib import Path
import numpy as np
import soundfile as sf
import tensorflow as tf
import tensorflow_hub as hub

# Variables and constants
MODEL_URL = "https://www.kaggle.com/models/google/bird-vocalization-classifier/frameworks/TensorFlow2/variations/perch_v2_cpu/versions/1"
TARGET_SR = 32000   # Perch expects files at 32 kHz
SAMPLES = 160000    # Perch Expects 5 second files, 5s @ 32 kHz = 160000
TOPK    = 3         # edit here if you want more/less labels per clip
BATCH   = 5         # edit here if you want adjust batching, 5 or less recommended for Pi 5

# Load the model
def load_model():
    t0 = time.perf_counter()    # Start timer
    m = hub.load(MODEL_URL)     # Load model from hub
    fn = m.signatures.get("serving_default", next(iter(m.signatures.values()))) # Get serving function
    input_name = list(fn.structured_input_signature[1].keys())[0]   # Get input tensor name
    return fn, input_name, time.perf_counter() - t0     # Return function, input name, and load time

# Read a single audio clip
def read_clip(p: Path):
    y, sr = sf.read(p, always_2d=False)
    if y.ndim > 1:  # if stereo, average to mono, from what I can tell perch expects a single channel file. 
        y = y.mean(axis=1)
    if sr != TARGET_SR:  # Check that sample rate matches expected
        raise ValueError(f"{p.name}: sr={sr} (expected {TARGET_SR})")
    if len(y) < SAMPLES:    # Check that audio is long enough, pad if needed
        y = np.pad(y, (0, SAMPLES - len(y)))
    else:
        y = y[:SAMPLES]
    return y.astype(np.float32)

# Apply softmax if needed
def _softmax_if_needed(arr):
    if (arr < 0).any():
        return tf.nn.softmax(arr, axis=-1).numpy()
    return arr

# Find score and label keys in model output
def _find_score_and_labels(outs):
    # Prefer typical keys; Perch exposes scores under 'label'
    for k in ("scores", "score", "probabilities", "probs", "logits", "label"):
        if k in outs: return k, None
    # Fallback: pick largest 2D float tensor
    bestk, best = None, None
    for k, v in outs.items():
        v = v.numpy() if isinstance(v, tf.Tensor) else v
        if getattr(v, "ndim", 0) == 2 and np.issubdtype(v.dtype, np.floating):
            if best is None or v.shape[1] > best.shape[1]:
                best, bestk = v, k
    return bestk, None

# Main
def main():
    if len(sys.argv) < 2:
        print("Usage: python perch2_min.py /path/to/clips [output_base]")
        sys.exit(1)
    clips_dir = Path(sys.argv[1])   # Input directory from command line
    out_base  = sys.argv[2] if len(sys.argv) > 2 else "perch_results"   # Output base name
    out_csv   = f"{out_base}.csv"   # add csv to out file
    out_stats = f"{out_base}_stats.txt" # Stats file name

    fn, input_name, load_s = load_model()   # Load model
    files = sorted([p for p in clips_dir.glob("**/*.wav")])  # Find all .wav files
    if not files:
        print("No .wav files found."); sys.exit(1)

    results, lat_ms = [], []    # Initialize results and latency lists
    io_s = infer_s = 0.0        # Initialize I/O and inference times
    wall0 = time.time()         # Start wall clock timer

    batch, names = [], []       # Initialize batch and names lists
    for p in files:             # Process each file
        t0 = time.perf_counter()    # Start timer
        try:                    # Read audio clip
            y = read_clip(p)
        except Exception as e:
            print(f"[skip] {e}")
            continue
        io_s += time.perf_counter() - t0    # Update I/O time

        batch.append(y); names.append(p)    # Add to batch and names
        if len(batch) == BATCH:             # If batch is full
            b = np.stack(batch, 0)          # Stack batch into a single tensor
            s = time.perf_counter()         # Start inference timer
            out = fn(**{input_name: tf.convert_to_tensor(b, tf.float32)})   # Run model inference
            dt = time.perf_counter() - s    # Measure inference time
            infer_s += dt                   # Update inference time
            per_item = (dt * 1000.0) / len(batch)   # Compute per-item latency

            outs = {k: (v.numpy() if isinstance(v, tf.Tensor) else v) for k, v in out.items()}  # Convert outputs to numpy
            score_key, label_arr = _find_score_and_labels(outs)     # Find score and label keys
            scores = _softmax_if_needed(outs[score_key])            # Apply softmax if needed

            # fast top-k
            idx = np.argpartition(-scores, kth=min(TOPK, scores.shape[1]-1), axis=1)[:, :TOPK]  # Find top-k indices
            for r, clip_path in enumerate(names):                       # Iterate over each clip
                ids = idx[r]; ids = ids[np.argsort(-scores[r, ids])]    # Sort top-k indices by score
                lat_ms.append(per_item)                                 # Append per-item latency
                for rank, i in enumerate(ids, 1):                       # Iterate over each top-k index
                    label = str(int(i))                                 # Perch usually outputs integer class labels
                    results.append([str(clip_path), rank, label, float(scores[r, i]), per_item])    # Append results

            batch.clear(); names.clear()        # Clear batch and names

    if batch:  # handle leftover files that don't perfectly match batch size
        b = np.stack(batch, 0)  
        s = time.perf_counter()
        out = fn(**{input_name: tf.convert_to_tensor(b, tf.float32)})
        dt = time.perf_counter() - s
        infer_s += dt
        per_item = (dt * 1000.0) / len(batch)

        outs = {k: (v.numpy() if isinstance(v, tf.Tensor) else v) for k, v in out.items()}
        score_key, label_arr = _find_score_and_labels(outs)
        scores = _softmax_if_needed(outs[score_key])

        idx = np.argpartition(-scores, kth=min(TOPK, scores.shape[1]-1), axis=1)[:, :TOPK]
        for r, clip_path in enumerate(names):
            ids = idx[r]; ids = ids[np.argsort(-scores[r, ids])]
            lat_ms.append(per_item)
            for rank, i in enumerate(ids, 1):
                label = str(int(i))
                results.append([str(clip_path), rank, label, float(scores[r, i]), per_item])

    wall = time.time() - wall0
    nclips = len({r[0] for r in results})

    # write CSV
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["file","rank","label","score","inference_ms"]); w.writerows(results)

    # write stats
    if lat_ms:
        lat = np.array(lat_ms, dtype=np.float32)
        mean = float(lat.mean()); med = float(np.median(lat))
        p90 = float(np.percentile(lat, 90)); p95 = float(np.percentile(lat, 95))
    else:
        mean = med = p90 = p95 = 0.0
    with open(out_stats, "w") as f:
        f.write(
            f"Files: {nclips}\nModel load: {load_s:.3f}s\nI/O: {io_s:.3f}s\n"
            f"Inference: {infer_s:.3f}s\nWall: {wall:.3f}s\n"
            f"Avg/clip: {mean:.1f} ms (median {med:.1f}, p90 {p90:.1f}, p95 {p95:.1f})\n"
            f"Throughput: {(nclips/wall if wall>0 else 0):.2f} clips/s (batch={BATCH})\n"
        )
    print(f"Done → {out_csv}, {out_stats}")

if __name__ == "__main__":
    main()
