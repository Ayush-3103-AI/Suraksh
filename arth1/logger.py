# logger.py
# Three-stream logging system for defense-grade demo
# A. Application Layer (stdout) - Authentication, clearance, access decisions
# B. Blockchain/Audit Layer (file + stdout) - Transactions, blocks, hashes
# C. Network Layer (stderr) - Binary conversion, bit manipulation, encryption

import logging
import sys
import os
from datetime import datetime

# Ensure log directory exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# ============================================================================
# A. APPLICATION LAYER LOGGER (stdout)
# ============================================================================
app_logger = logging.getLogger("app")
app_logger.setLevel(logging.INFO)
app_handler = logging.StreamHandler(sys.stdout)
app_handler.setFormatter(logging.Formatter(
    '[APPLICATION] %(asctime)s | %(message)s',
    datefmt='%H:%M:%S'
))
app_logger.addHandler(app_handler)
app_logger.propagate = False


# ============================================================================
# B. BLOCKCHAIN/AUDIT LAYER LOGGER (file + stdout)
# ============================================================================
chain_logger = logging.getLogger("chain")
chain_logger.setLevel(logging.INFO)

# File handler for persistent audit log
chain_file_handler = logging.FileHandler(
    os.path.join(LOG_DIR, "blockchain_audit.log"),
    mode='a'
)
chain_file_handler.setFormatter(logging.Formatter(
    '%(asctime)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))

# Console handler for real-time blockchain events
chain_console_handler = logging.StreamHandler(sys.stdout)
chain_console_handler.setFormatter(logging.Formatter(
    '[BLOCKCHAIN] %(asctime)s | %(message)s',
    datefmt='%H:%M:%S'
))

chain_logger.addHandler(chain_file_handler)
chain_logger.addHandler(chain_console_handler)
chain_logger.propagate = False


# ============================================================================
# C. NETWORK LAYER LOGGER (stderr)
# ============================================================================
network_logger = logging.getLogger("network")
network_logger.setLevel(logging.INFO)
network_handler = logging.StreamHandler(sys.stderr)
network_handler.setFormatter(logging.Formatter(
    '[NETWORK] %(asctime)s | %(message)s',
    datefmt='%H:%M:%S'
))
network_logger.addHandler(network_handler)
network_logger.propagate = False


# ============================================================================
# Convenience functions for structured logging
# ============================================================================

def log_app(message: str):
    """Application layer: authentication, clearance decisions, access control."""
    app_logger.info(message)


def log_chain(message: str):
    """Blockchain layer: transactions, blocks, hashes, audit events."""
    chain_logger.info(message)


def log_network(message: str):
    """Network layer: binary conversion, bit manipulation, encryption, chunking."""
    network_logger.info(message)
