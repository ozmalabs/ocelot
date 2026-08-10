//! softmax_classifier draft for op `lexical_access` — AUTHORED by the
//! agent's code-writing cortex (target it selected: lexical_access;
//! pattern it selected: softmax_classifier; language it selected: rust).
//!
//! The agent's CURRENT lexical_access is NON-PARAMETRIC: it compares an
//! input A1-envelope trajectory against stored AcousticSign trajectories
//! by cosine distance (1-NN with online cluster creation). This draft
//! re-expresses recognition as a PARAMETRIC map:
//!
//!     logits = W · x + b          (linear_layer to n_classes)
//!     P      = softmax(logits)     (probability over word classes)
//!     y_hat  = argmax_c P[c]
//!
//! Input  x : the fixed-length trajectory feature vector the op already
//!            assembles — TRAJ_SAMPLES (32) frames x N_PATCHES (25) =
//!            FEAT_DIM channels, flattened.
//! Output   : the predicted class index in [0, N_CLASSES).
//!
//! BOUNDARY (authored, not trained): the weight table `W`/`B` below is
//! the net's competence. Fitting it requires a training step
//! (cross_entropy_loss + gradient descent over labelled audio) — the
//! recipe's own `mechanism` says "train with cross_entropy_loss". The
//! agent AUTHORS this structure; it does not run that fitting loop. So
//! `W`/`B` ship UNFITTED (zeros): the forward pass is real and complete,
//! but the net is an artifact the agent reasons FROM, not a trained
//! drop-in for the hand-built recogniser. With W=0 every logit is equal
//! and the net predicts class 0 — the honest signature of "structure
//! present, parameters absent."

pub const TRAJ_SAMPLES: usize = 32;
pub const N_PATCHES: usize = 25;
pub const FEAT_DIM: usize = TRAJ_SAMPLES * N_PATCHES; // 800
pub const N_CLASSES: usize = 11; // ten digits + unknown

// Parameters. These ARE the learned content of the net. Authoring fills
// in the SHAPE; a training step the agent does not perform would fill in
// the VALUES. Left at zero — unfitted on purpose.
pub static W: [[f32; FEAT_DIM]; N_CLASSES] = [[0.0; FEAT_DIM]; N_CLASSES];
pub static B: [f32; N_CLASSES] = [0.0; N_CLASSES];

/// softmax_classifier forward pass: features -> class index.
/// Pure function of the input and the (unfitted) parameters.
#[no_mangle]
pub extern "C" fn lexical_access_softmax(feats: *const f32, len: usize) -> i32 {
    if feats.is_null() || len < FEAT_DIM {
        return -1;
    }
    let x: &[f32] = unsafe { std::slice::from_raw_parts(feats, FEAT_DIM) };

    // linear_layer: logits = W·x + b
    let mut logits = [0.0f32; N_CLASSES];
    for c in 0..N_CLASSES {
        let row = &W[c];
        let mut acc = B[c];
        for i in 0..FEAT_DIM {
            acc += row[i] * x[i];
        }
        logits[c] = acc;
    }

    // softmax (numerically stabilised) — then argmax. We only need the
    // argmax for the class decision, but compute the distribution so the
    // forward pass is the genuine softmax_classifier, not a bare argmax.
    let mut maxv = f32::NEG_INFINITY;
    for &l in logits.iter() {
        if l > maxv {
            maxv = l;
        }
    }
    let mut denom = 0.0f32;
    for &l in logits.iter() {
        denom += (l - maxv).exp();
    }
    let mut best = 0usize;
    let mut best_p = -1.0f32;
    for c in 0..N_CLASSES {
        let p = (logits[c] - maxv).exp() / denom;
        if p > best_p {
            best_p = p;
            best = c;
        }
    }
    best as i32
}
