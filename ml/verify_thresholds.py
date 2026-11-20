"""
Threshold leakage audit: prove thresholds were computed only on training-split reals.
"""
import numpy as np
import sys

y   = np.load('ml/data/cache/labels.npy')
gen = np.load('ml/data/cache/generators.npy', allow_pickle=True)

# --- Reproduce the EXACT same split logic as train.py (same seed, same ops) ---
real_indices = np.where(gen == 'real')[0]
np.random.seed(42)
shuffled_reals = np.random.permutation(real_indices)
n_heldout_reals = len(shuffled_reals) // 4
heldout_real_idx = shuffled_reals[:n_heldout_reals]
train_real_idx   = shuffled_reals[n_heldout_reals:]

heldout_fake_idx = np.where(gen == 'flux')[0]
test_idx = np.concatenate([heldout_real_idx, heldout_fake_idx])

train_fake_idx = np.where(np.isin(gen, ['stable_diffusion', 'midjourney', 'dalle']))[0]
all_train_idx = np.concatenate([train_real_idx, train_fake_idx])
# train.py calls np.random.shuffle(all_train_idx) AFTER the seed-42 permutation above.
# The shuffle has no second seed, so it uses the ongoing state from the np.random.seed(42) call.
np.random.shuffle(all_train_idx)   # state flows from seed(42) exactly as in train.py
split_pt  = int(0.75 * len(all_train_idx))
train_idx = all_train_idx[:split_pt]
val_idx   = all_train_idx[split_pt:]

val_real_mask    = (y[val_idx] == 0)
val_real_indices = val_idx[val_real_mask]

overlap_with_held_reals = np.intersect1d(val_real_indices, heldout_real_idx)
overlap_with_flux       = np.intersect1d(val_idx, heldout_fake_idx)

print("=== THRESHOLD LEAKAGE AUDIT ===")
print(f"Total samples                : {len(y)}")
print(f"Real samples total           : {len(real_indices)}")
print(f"  -> Held-out reals (25%)    : {len(heldout_real_idx)}")
print(f"  -> Train-split reals (75%) : {len(train_real_idx)}")
print(f"Flux (held-out fakes)        : {len(heldout_fake_idx)}")
print(f"test_idx size                : {len(test_idx)}")
print(f"train_idx size               : {len(train_idx)}")
print(f"val_idx size                 : {len(val_idx)}")
print(f"  val reals                  : {val_real_mask.sum()}")
print(f"  val fakes                  : {(~val_real_mask).sum()}")
print()
print(f"Overlap: val reals ∩ held-out reals : {len(overlap_with_held_reals)}")
print(f"Overlap: val_idx   ∩ flux fakes     : {len(overlap_with_flux)}")
print()
if len(overlap_with_held_reals) == 0 and len(overlap_with_flux) == 0:
    print("VERDICT: NO LEAKAGE. Thresholds computed on training-split reals only.")
    sys.exit(0)
else:
    print("VERDICT: LEAKAGE DETECTED -- thresholds must be recomputed.")
    sys.exit(1)
