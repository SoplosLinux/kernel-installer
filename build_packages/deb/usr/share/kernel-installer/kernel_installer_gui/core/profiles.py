from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List
# Standard gettext marker for string extraction without immediate translation
def _(s): return s


class ProfileType(Enum):
    """Available kernel profile types."""
    GAMING = auto()
    AUDIO_VIDEO = auto()
    MINIMAL = auto()
    CUSTOM = auto()


@dataclass
class KernelProfile:
    """
    A kernel configuration profile with optimized settings.
    
    Attributes:
        name: Display name of the profile
        suffix: Short name for kernel suffix (no spaces, no special chars)
        description: Detailed description
        icon: Icon name for the UI
        config_options: Dict of CONFIG_* options to set
        modules_to_disable: List of modules to disable for minimal builds
    """
    id: ProfileType
    name: str
    suffix: str  # Clean name for kernel suffix
    description: str
    icon: str
    config_options: Dict[str, str] = field(default_factory=dict)
    modules_to_disable: List[str] = field(default_factory=list)
    
    def apply_to_config(self, config_path: str) -> None:
        """
        Apply this profile's settings to a kernel .config file.
        
        Args:
            config_path: Path to the .config file to modify
        """
        # Read existing config
        with open(config_path, 'r') as f:
            lines = f.readlines()
        
        # Build a dict of existing options
        config = {}
        for line in lines:
            line = line.strip()
            if line.startswith('CONFIG_'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value
                elif line.endswith(' is not set'):
                    key = line.replace('# ', '').replace(' is not set', '')
                    config[key] = 'n'
        
        # Apply profile options
        for key, value in self.config_options.items():
            config[key] = value
        
        # Disable specified modules
        for module in self.modules_to_disable:
            config[f'CONFIG_{module}'] = 'n'
        
        # Write back
        with open(config_path, 'w') as f:
            for key, value in sorted(config.items()):
                if value == 'n':
                    f.write(f'# {key} is not set\n')
                else:
                    f.write(f'{key}={value}\n')


# Predefined kernel profiles
KERNEL_PROFILES = {
    ProfileType.GAMING: KernelProfile(
        id=ProfileType.GAMING,
        name=_("Gaming"),
        suffix="gaming",
        description=_(
            "Optimized for games with low input latency, "
            "high CPU performance and better GPU management. "
            "Ideal for gamers and streaming."
        ),
        icon="input-gaming",
        config_options={
            # Preemption settings for responsiveness
            'CONFIG_PREEMPT': 'y',
            'CONFIG_PREEMPT_VOLUNTARY': 'n',
            'CONFIG_PREEMPT_NONE': 'n',
            
            # High timer frequency for lower latency
            'CONFIG_HZ_1000': 'y',
            'CONFIG_HZ_300': 'n',
            'CONFIG_HZ_250': 'n',
            'CONFIG_HZ_100': 'n',
            'CONFIG_HZ': '1000',
            
            # CPU frequency scaling for performance
            'CONFIG_CPU_FREQ_GOV_PERFORMANCE': 'y',
            'CONFIG_CPU_FREQ_DEFAULT_GOV_PERFORMANCE': 'y',
            
            # Disable CPU frequency tracking overhead
            'CONFIG_CPU_FREQ_STAT': 'n',
            
            # Better memory management for games
            'CONFIG_TRANSPARENT_HUGEPAGE': 'y',
            'CONFIG_TRANSPARENT_HUGEPAGE_ALWAYS': 'y',
            
            # Disable debugging (performance overhead)
            'CONFIG_DEBUG_INFO': 'n',
            'CONFIG_DEBUG_KERNEL': 'n',
            'CONFIG_FTRACE': 'n',
            
            # Better I/O scheduler for NVMe/SSD
            'CONFIG_MQ_IOSCHED_DEADLINE': 'y',
            'CONFIG_MQ_IOSCHED_KYBER': 'y',
            
            # Enable FUTEX for better game threading
            'CONFIG_FUTEX': 'y',
            'CONFIG_FUTEX_PI': 'y',
        }
    ),
    
    ProfileType.AUDIO_VIDEO: KernelProfile(
        id=ProfileType.AUDIO_VIDEO,
        name=_("Audio/Video"),
        suffix="lowlatency",
        description=_(
            "Low-latency kernel for audio and video production. "
            "Optimized for DAWs, video editing and professional streaming. "
            "Uses real-time preemption for ultra-low latency."
        ),
        icon="audio-card",
        config_options={
            # Full preemption for lowest latency
            'CONFIG_PREEMPT': 'y',
            'CONFIG_PREEMPT_VOLUNTARY': 'n',
            'CONFIG_PREEMPT_NONE': 'n',
            
            # Real-time features
            'CONFIG_PREEMPT_RT': 'y',
            'CONFIG_PREEMPT_RT_FULL': 'y',
            
            # Highest timer frequency
            'CONFIG_HZ_1000': 'y',
            'CONFIG_HZ': '1000',
            
            # Tickless for reduced interruptions
            'CONFIG_NO_HZ_FULL': 'y',
            'CONFIG_NO_HZ': 'y',
            
            # High resolution timers
            'CONFIG_HIGH_RES_TIMERS': 'y',
            
            # Real-time scheduling
            'CONFIG_RT_GROUP_SCHED': 'y',
            
            # Disable power management that could cause audio glitches
            'CONFIG_CPU_IDLE': 'n',
            
            # USB audio support
            'CONFIG_SND_USB_AUDIO': 'y',
            
            # Firewire audio
            'CONFIG_SND_FIREWIRE': 'y',
            
            # Disable debugging
            'CONFIG_DEBUG_INFO': 'n',
            'CONFIG_DEBUG_KERNEL': 'n',
        }
    ),
    
    ProfileType.MINIMAL: KernelProfile(
        id=ProfileType.MINIMAL,
        name=_("Minimal / Office"),
        suffix="minimal",
        description=_(
            "Lightweight kernel for office work, web browsing and general use. "
            "No unnecessary modules, low resource consumption. "
            "Ideal for older hardware or virtual machines."
        ),
        icon="applications-office",
        config_options={
            # Voluntary preemption (balanced)
            'CONFIG_PREEMPT_VOLUNTARY': 'y',
            'CONFIG_PREEMPT': 'n',
            
            # Lower timer frequency (less CPU usage)
            'CONFIG_HZ_250': 'y',
            'CONFIG_HZ': '250',
            
            # Power saving
            'CONFIG_CPU_FREQ_GOV_POWERSAVE': 'y',
            'CONFIG_CPU_FREQ_GOV_ONDEMAND': 'y',
            'CONFIG_CPU_IDLE': 'y',
            
            # Disable debugging
            'CONFIG_DEBUG_INFO': 'n',
            'CONFIG_DEBUG_KERNEL': 'n',
            'CONFIG_FTRACE': 'n',
            'CONFIG_KPROBES': 'n',
            
            # Disable unused features
            'CONFIG_PROFILING': 'n',
            'CONFIG_OPROFILE': 'n',
        },
        modules_to_disable=[
            # Gaming hardware not needed
            'JOYSTICK',
            'GAMEPORT',
            
            # Exotic filesystems
            'BTRFS_FS',
            'XFS_FS',
            'REISERFS_FS',
            'JFS_FS',
            'NILFS2_FS',
            
            # Exotic network protocols
            'ATALK',
            'IPX',
            'DECNET',
            
            # Amateur radio
            'HAMRADIO',
            
            # IrDA
            'IRDA',
        ]
    ),
}


def get_profile(profile_type: ProfileType) -> KernelProfile:
    """Get a kernel profile by type."""
    return KERNEL_PROFILES.get(profile_type)


def get_all_profiles() -> List[KernelProfile]:
    """Get all available kernel profiles."""
    return list(KERNEL_PROFILES.values())
