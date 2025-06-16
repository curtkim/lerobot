import torch
import time
from lerobot.common.policies.smolvla.modeling_smolvla import SmolVLAPolicy
from lerobot.common.policies.smolvla.configuration_smolvla import SmolVLAConfig
from transformers import AutoProcessor
 
# Load model (replace with your checkpoint if needed)
# Try loading from HuggingFace Hub instead of local path
policy = SmolVLAPolicy.from_pretrained("lerobot/smolvla_base")
policy.eval()

# Check if normalize_inputs has stats loaded
print("Checking normalization stats...")
if hasattr(policy, 'normalize_inputs'):
    for attr in dir(policy.normalize_inputs):
        if attr.startswith('buffer_'):
            buffer = getattr(policy.normalize_inputs, attr)
            print(f"{attr}: {buffer if buffer is None else 'loaded'}")
 
# patch: The loaded policy is missing the language_tokenizer attribute.
policy.language_tokenizer = AutoProcessor.from_pretrained(policy.config.vlm_model_name).tokenizer
 
# Dummy batch config for a single observation
batch_size = 1
img_shape = (3, 256, 256)  # (C, H, W)
# Infer state_dim from the loaded normalization stats
state_dim = policy.normalize_inputs.buffer_observation_state.mean.shape[-1]
 
dummy_batch = {
    # a single image observation
    "observation.image": torch.rand(batch_size, *img_shape),
    "observation.image2": torch.rand(batch_size, *img_shape),
    "observation.image3": torch.rand(batch_size, *img_shape),
    # a single state observation
    "observation.state": torch.rand(batch_size, state_dim),
    "task": ["stack the blocks"] * batch_size,
}
 
# --- Prepare inputs for the model ---
# The policy expects normalized inputs and specific data preparation.
# Skip normalization if stats are not available
try:
    normalized_batch = policy.normalize_inputs(dummy_batch)
except AssertionError:
    print("Warning: Normalization stats not available, creating dummy stats")
    
    # Create dummy statistics for normalization
    dummy_stats = {}
    
    # For state observations
    if "observation.state" in dummy_batch:
        state_dim = dummy_batch["observation.state"].shape[-1]
        dummy_stats["observation.state"] = {
            "mean": torch.zeros(state_dim),
            "std": torch.ones(state_dim),
            "min": torch.zeros(state_dim) - 1,
            "max": torch.zeros(state_dim) + 1,
        }
    
    # For image observations (visual features use IDENTITY normalization, so no stats needed)
    # But we'll add them just in case
    for key in ["observation.image", "observation.image2", "observation.image3"]:
        if key in dummy_batch:
            dummy_stats[key] = {
                "mean": torch.tensor([0.0, 0.0, 0.0]).reshape(3, 1, 1),
                "std": torch.tensor([1.0, 1.0, 1.0]).reshape(3, 1, 1),
                "min": torch.tensor([0.0, 0.0, 0.0]).reshape(3, 1, 1),
                "max": torch.tensor([1.0, 1.0, 1.0]).reshape(3, 1, 1),
            }
    
    # For actions
    action_dim = 6  # Typical for SO101
    dummy_stats["action"] = {
        "mean": torch.zeros(action_dim),
        "std": torch.ones(action_dim),
        "min": torch.zeros(action_dim) - 1,
        "max": torch.zeros(action_dim) + 1,
    }
    
    # Load dummy stats into the policy
    # The state dict expects keys in the format "buffer_{key.replace('.', '_')}.{stat}"
    state_dict = {}
    for key, stats in dummy_stats.items():
        buffer_key = key.replace('.', '_')
        for stat_name, stat_value in stats.items():
            state_dict[f"buffer_{buffer_key}.{stat_name}"] = stat_value
    
    policy.normalize_inputs.load_state_dict(state_dict, strict=False)
    policy.normalize_targets.load_state_dict(state_dict, strict=False)
    policy.unnormalize_outputs.load_state_dict(state_dict, strict=False)
    
    # Try again with dummy stats
    normalized_batch = policy.normalize_inputs(dummy_batch)

images, img_masks = policy.prepare_images(normalized_batch)
state = policy.prepare_state(normalized_batch)
lang_tokens, lang_masks = policy.prepare_language(normalized_batch)
# ---
 
# Warmup
for _ in range(3):
    with torch.no_grad():
        _ = policy.model.sample_actions(images, img_masks, lang_tokens, lang_masks, state)
 
# Benchmark
#torch.cuda.reset_peak_memory_stats()
start = time.time()
for idx in range(10):
    print(idx)
    with torch.no_grad():
        _ = policy.model.sample_actions(images, img_masks, lang_tokens, lang_masks, state)
end = time.time()
 
print(f"Avg inference time: {(end - start)/100:.6f} s")
