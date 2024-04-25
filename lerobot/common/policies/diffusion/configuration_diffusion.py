from dataclasses import dataclass, field


@dataclass
class DiffusionConfig:
    """Configuration class for Diffusion Policy.

    Defaults are configured for training with PushT providing proprioceptive and single camera observations.

    The parameters you will most likely need to change are the ones which depend on the environment / sensors.
    Those are: `state_dim`, `action_dim` and `image_size`.

    Args:
        state_dim: Dimensionality of the observation state space (excluding images).
        action_dim: Dimensionality of the action space.
        image_size: (H, W) size of the input images.
        n_obs_steps: Number of environment steps worth of observations to pass to the policy (takes the
            current step and additional steps going back).
        horizon: Diffusion model action prediction size as detailed in `DiffusionPolicy.select_action`.
        n_action_steps: The number of action steps to run in the environment for one invocation of the policy.
            See `DiffusionPolicy.select_action` for more details.
        input_shapes: A dictionary defining the shapes of the input data for the policy.
            The key represents the input data name, and the value is a list indicating the dimensions
            of the corresponding data. For example, "observation.image" refers to an input from
            a camera with dimensions [3, 96, 96], indicating it has three color channels and 96x96 resolution.
            Importantly, shapes doesnt include batch dimension or temporal dimension.
        output_shapes: A dictionary defining the shapes of the output data for the policy.
            The key represents the output data name, and the value is a list indicating the dimensions
            of the corresponding data. For example, "action" refers to an output shape of [14], indicating
            14-dimensional actions. Importantly, shapes doesnt include batch dimension or temporal dimension.
        normalize_input_modes: A dictionary with key represents the modality (e.g. "observation.state"),
            and the value specifies the normalization mode to apply. The two availables
            modes are "mean_std" which substracts the mean and divide by the standard
            deviation and "min_max" which rescale in a [-1, 1] range.
        unnormalize_output_modes: Similar dictionary as `normalize_input_modes`, but to unormalize in original scale.
        vision_backbone: Name of the torchvision resnet backbone to use for encoding images.
        crop_shape: (H, W) shape to crop images to as a preprocessing step for the vision backbone. Must fit
            within the image size. If None, no cropping is done.
        crop_is_random: Whether the crop should be random at training time (it's always a center crop in eval
            mode).
        use_pretrained_backbone: Whether the backbone should be initialized with pretrained weights from
            torchvision.
        use_group_norm: Whether to replace batch normalization with group normalization in the backbone.
            The group sizes are set to be about 16 (to be precise, feature_dim // 16).
        spatial_softmax_num_keypoints: Number of keypoints for SpatialSoftmax.
        down_dims: Feature dimension for each stage of temporal downsampling in the diffusion modeling Unet.
            You may provide a variable number of dimensions, therefore also controlling the degree of
            downsampling.
        kernel_size: The convolutional kernel size of the diffusion modeling Unet.
        n_groups: Number of groups used in the group norm of the Unet's convolutional blocks.
        diffusion_step_embed_dim: The Unet is conditioned on the diffusion timestep via a small non-linear
            network. This is the output dimension of that network, i.e., the embedding dimension.
        use_film_scale_modulation: FiLM (https://arxiv.org/abs/1709.07871) is used for the Unet conditioning.
            Bias modulation is used be default, while this parameter indicates whether to also use scale
            modulation.
        num_train_timesteps: Number of diffusion steps for the forward diffusion schedule.
        beta_schedule: Name of the diffusion beta schedule as per DDPMScheduler from Hugging Face diffusers.
        beta_start: Beta value for the first forward-diffusion step.
        beta_end: Beta value for the last forward-diffusion step.
        prediction_type: The type of prediction that the diffusion modeling Unet makes. Choose from "epsilon"
            or "sample". These have equivalent outcomes from a latent variable modeling perspective, but
            "epsilon" has been shown to work better in many deep neural network settings.
        clip_sample: Whether to clip the sample to [-`clip_sample_range`, +`clip_sample_range`] for each
            denoising step at inference time. WARNING: you will need to make sure your action-space is
            normalized to fit within this range.
        clip_sample_range: The magnitude of the clipping range as described above.
        num_inference_steps: Number of reverse diffusion steps to use at inference time (steps are evenly
            spaced). If not provided, this defaults to be the same as `num_train_timesteps`.
    """

    # Environment.
    # Inherit these from the environment config.
    # TODO(rcadene, alexander-soare): remove these as they are defined in input_shapes, output_shapes
    state_dim: int = 2
    action_dim: int = 2
    image_size: tuple[int, int] = (96, 96)

    # Inputs / output structure.
    n_obs_steps: int = 2
    horizon: int = 16
    n_action_steps: int = 8

    input_shapes: dict[str, list[str]] = field(
        default_factory=lambda: {
            "observation.image": [3, 96, 96],
            "observation.state": [2],
        }
    )
    output_shapes: dict[str, list[str]] = field(
        default_factory=lambda: {
            "action": [2],
        }
    )

    # Normalization / Unnormalization
    normalize_input_modes: dict[str, str] = field(
        default_factory=lambda: {
            "observation.image": "mean_std",
            "observation.state": "min_max",
        }
    )
    unnormalize_output_modes: dict[str, str] = field(
        default_factory=lambda: {
            "action": "min_max",
        }
    )

    # Architecture / modeling.
    # Vision backbone.
    vision_backbone: str = "resnet18"
    crop_shape: tuple[int, int] | None = (84, 84)
    crop_is_random: bool = True
    use_pretrained_backbone: bool = False
    use_group_norm: bool = True
    spatial_softmax_num_keypoints: int = 32
    # Unet.
    down_dims: tuple[int, ...] = (512, 1024, 2048)
    kernel_size: int = 5
    n_groups: int = 8
    diffusion_step_embed_dim: int = 128
    use_film_scale_modulation: bool = True
    # Noise scheduler.
    num_train_timesteps: int = 100
    beta_schedule: str = "squaredcos_cap_v2"
    beta_start: float = 0.0001
    beta_end: float = 0.02
    prediction_type: str = "epsilon"
    clip_sample: bool = True
    clip_sample_range: float = 1.0

    # Inference
    num_inference_steps: int | None = None

    # ---
    # TODO(alexander-soare): Remove these from the policy config.
    batch_size: int = 64
    grad_clip_norm: int = 10
    lr: float = 1.0e-4
    lr_scheduler: str = "cosine"
    lr_warmup_steps: int = 500
    adam_betas: tuple[float, float] = (0.95, 0.999)
    adam_eps: float = 1.0e-8
    adam_weight_decay: float = 1.0e-6
    utd: int = 1
    use_ema: bool = True
    ema_update_after_step: int = 0
    ema_min_alpha: float = 0.0
    ema_max_alpha: float = 0.9999
    ema_inv_gamma: float = 1.0
    ema_power: float = 0.75

    def __post_init__(self):
        """Input validation (not exhaustive)."""
        if not self.vision_backbone.startswith("resnet"):
            raise ValueError(
                f"`vision_backbone` must be one of the ResNet variants. Got {self.vision_backbone}."
            )
        if self.crop_shape[0] > self.image_size[0] or self.crop_shape[1] > self.image_size[1]:
            raise ValueError(
                f"`crop_shape` should fit within `image_size`. Got {self.crop_shape} for `crop_shape` and "
                f"{self.image_size} for `image_size`."
            )
        supported_prediction_types = ["epsilon", "sample"]
        if self.prediction_type not in supported_prediction_types:
            raise ValueError(
                f"`prediction_type` must be one of {supported_prediction_types}. Got {self.prediction_type}."
            )