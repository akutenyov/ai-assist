"""AI Assist application package.

Runtime preparation runs before submodules import third-party SDKs. This keeps
the application independent from paths injected by other local projects.
"""

from .environment import configure_runtime


configure_runtime()
