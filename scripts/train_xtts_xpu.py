"""FINE-TUNE XTTS-v2 on ONE speaker, on the Intel Arc B580 (XPU) — via a cuda->xpu shim over Coqui's CUDA-only trainer.

The Coqui Trainer is CUDA-hardcoded AND torch.cuda.is_available() is False here -> it would fall to CPU. This shim tricks it
into "GPU mode" and redirects every cuda op (.cuda(), to_cuda, empty_cache, autocast/scaler) to XPU, with mixed-precision OFF
(avoids the autocast/GradScaler device traps). Data = one LibriTTS speaker (24kHz, transcripts); hold out N_TEST utterances for
the post-finetune FFT/WavLM compare. Short run to prove it TRAINS on the B580 + tightens the clone.

Run (XPU venv):
  XTTS_FT=<outdir> <xpu-venv>/bin/python scripts/train_xtts_xpu.py
"""
import os
import sys
import glob
import functools

# ---------------- cuda -> xpu shim (MUST be before TTS/trainer import) ----------------
import torch
assert torch.xpu.is_available(), "no XPU"
_DEV = "xpu"
torch.cuda.is_available = lambda: True
torch.cuda.device_count = lambda: 1
torch.cuda.current_device = lambda: 0
torch.cuda.set_device = lambda *a, **k: None
torch.cuda.empty_cache = lambda: torch.xpu.empty_cache()
torch.cuda.synchronize = lambda *a, **k: torch.xpu.synchronize()
torch.cuda.get_device_name = lambda *a, **k: "Intel Arc B580 (XPU)"
torch.cuda.get_device_properties = lambda *a, **k: torch.xpu.get_device_properties(0)
try:
    torch.cuda.get_rng_state = lambda *a, **k: torch.xpu.get_rng_state()
    torch.cuda.set_rng_state = lambda s, *a, **k: torch.xpu.set_rng_state(s)
    torch.cuda.manual_seed_all = lambda s: torch.xpu.manual_seed_all(s)
except Exception:
    pass
_mod_cuda = torch.nn.Module.cuda
torch.nn.Module.cuda = lambda self, *a, **k: self.to(_DEV)
torch.Tensor.cuda = lambda self, *a, **k: self.to(_DEV)

import numpy as np
import soundfile as sf

LIBRITTS = "/home/matt/data/LibriTTS/test-clean"
XTTS = os.path.expanduser("~/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2")
OUT = os.environ.get("XTTS_FT", "/tmp/claude-1000/-home-matt-ozma-internal-research-experiments-gamma-substrate/"
                     "c0315161-a04e-4a46-9c86-b2c94e589dbb/scratchpad/xtts_ft")
N_TEST = 10
MIN_DUR, MAX_DUR = 2.0, 7.0
EPOCHS = int(os.environ.get("FT_EPOCHS", "6"))
BATCH = int(os.environ.get("FT_BATCH", "1"))
UNFREEZE_LAST = int(os.environ.get("FT_UNFREEZE", "2"))   # train only the last N GPT blocks + heads (B580 12GB VRAM)


def build_samples(speaker):
    rows = []
    for wav in sorted(glob.glob(os.path.join(LIBRITTS, speaker, "**", "*.wav"), recursive=True)):
        txtf = wav.replace(".wav", ".normalized.txt")
        if not os.path.exists(txtf):
            continue
        info = sf.info(wav)
        if not (MIN_DUR <= info.duration <= MAX_DUR):
            continue
        text = open(txtf).read().strip()
        if len(text) < 4:
            continue
        rows.append({"audio_file": wav, "text": text, "speaker_name": speaker, "language": "en"})
    return rows


def main():
    os.makedirs(OUT, exist_ok=True)
    # pick the speaker with the most usable audio
    best = None
    for sp in sorted(os.listdir(LIBRITTS)):
        r = build_samples(sp)
        if best is None or len(r) > len(best[1]):
            best = (sp, r)
    speaker, rows = best
    test = rows[:N_TEST]; train = rows[N_TEST:-5] or rows[N_TEST:]; eval_s = rows[-5:]
    # save held-out test (audio) for the post-finetune compare
    for i, r in enumerate(test):
        x, sr = sf.read(r["audio_file"], dtype="float32")
        sf.write(os.path.join(OUT, f"test_real_{i}.wav"), x, sr)
    import json
    json.dump({"speaker": speaker, "test_texts": [r["text"] for r in test],
               "reference": rows[N_TEST]["audio_file"]}, open(os.path.join(OUT, "ft_manifest.json"), "w"), indent=1)
    print(f"  speaker {speaker}: {len(train)} train / {len(eval_s)} eval / {len(test)} held-out test utterances")

    # ---------------- XTTS GPT fine-tune config ----------------
    from TTS.tts.layers.xtts.trainer.gpt_trainer import GPTArgs, GPTTrainer, GPTTrainerConfig
    from TTS.tts.models.xtts import XttsAudioConfig
    from trainer import Trainer, TrainerArgs
    import trainer.trainer as trmod
    trmod.to_cuda = lambda x: x.to(_DEV) if hasattr(x, "to") else x      # redirect batch moves to XPU

    model_args = GPTArgs(
        max_conditioning_length=88200, min_conditioning_length=44100, max_wav_length=154350, max_text_length=200,
        mel_norm_file=os.path.join(XTTS, "mel_stats.pth"), dvae_checkpoint=os.path.join(XTTS, "dvae.pth"),
        xtts_checkpoint=os.path.join(XTTS, "model.pth"), tokenizer_file=os.path.join(XTTS, "vocab.json"),
        gpt_num_audio_tokens=1026, gpt_start_audio_token=1024, gpt_stop_audio_token=1025,
        gpt_use_masking_gt_prompt_approach=True, gpt_use_perceiver_resampler=True)
    audio = XttsAudioConfig(sample_rate=22050, dvae_sample_rate=22050, output_sample_rate=24000)
    config = GPTTrainerConfig(
        output_path=OUT, model_args=model_args, audio=audio, run_name="ft_xpu",
        epochs=EPOCHS, batch_size=BATCH, batch_group_size=BATCH * 4, eval_batch_size=BATCH,
        num_loader_workers=2, eval_split_max_size=64, print_step=10, save_step=100000, save_n_checkpoints=1,
        save_checkpoints=True, optimizer="AdamW", optimizer_params={"betas": [0.9, 0.96], "eps": 1e-8, "weight_decay": 1e-2},
        lr=5e-6, lr_scheduler="MultiStepLR", lr_scheduler_params={"milestones": [900000], "gamma": 0.5},
        mixed_precision=False)

    model = GPTTrainer.init_from_config(config)

    # ---- FREEZE most of the GPT (B580 12GB VRAM): train only the last UNFREEZE_LAST blocks + output heads ----
    import re
    names = [n for n, _ in model.named_parameters()]
    layer_nums = sorted({int(m.group(1)) for n in names for m in [re.search(r"\.h\.(\d+)\.", n)] if m})
    keep = set(layer_nums[-UNFREEZE_LAST:]) if layer_nums else set()
    for p in model.parameters():
        p.requires_grad_(False)
    for n, p in model.named_parameters():
        if any(f".h.{k}." in n for k in keep) or any(t in n for t in ("mel_head", "text_head", "final_norm", "ln_f")):
            p.requires_grad_(True)
    ntr = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  GPT has {len(layer_nums)} blocks; unfreezing last {UNFREEZE_LAST} {sorted(keep)} + heads -> "
          f"{ntr/1e6:.0f}M trainable / {sum(p.numel() for p in model.parameters())/1e6:.0f}M total", flush=True)

    tr = Trainer(TrainerArgs(restore_path=None, skip_train_epoch=False, grad_accum_steps=1),
                 config, output_path=OUT, model=model, train_samples=train, eval_samples=eval_s)
    print(f"  trainer device: use_cuda={tr.use_cuda}; training {EPOCHS} epochs on the B580...", flush=True)
    tr.fit()
    print("  FINE-TUNE DONE. best/last checkpoint in", OUT)


if __name__ == "__main__":
    main()
