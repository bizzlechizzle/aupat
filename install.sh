#!/usr/bin/env bash
#
# AUPAT v0.1.2 Installation Script
#
# Bulletproof installation for macOS and Linux
# Detects OS, installs dependencies, sets up Python environment
#
# Usage:
#   ./install.sh [--skip-docker]
#
# Options:
#   --skip-docker   Skip Docker installation check (for CI/testing)
#
# Principles: KISS, BPL, BPA, DRETW
# Idempotent: Safe to run multiple times
#

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Options
SKIP_DOCKER=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-docker)
            SKIP_DOCKER=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--skip-docker]"
            exit 1
            ;;
    esac
done

echo "========================================="
echo "AUPAT v0.1.2 Installation"
echo "========================================="
echo ""

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macOS"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [[ -f /etc/os-release ]]; then
            . /etc/os-release
            echo "$ID"
        else
            echo "linux"
        fi
    else
        echo "unknown"
    fi
}

OS=$(detect_os)
echo "Detected OS: $OS"
echo ""

# Check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Print status message
print_status() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# macOS installation
install_macos() {
    echo "========================================="
    echo "macOS Installation"
    echo "========================================="
    echo ""

    # Check for Homebrew
    if ! command_exists brew; then
        echo "Homebrew not found. Installing Homebrew..."
        echo ""
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # Add Homebrew to PATH for Apple Silicon Macs
        if [[ -f /opt/homebrew/bin/brew ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    else
        print_status "Homebrew already installed"
    fi

    # Update Homebrew
    echo ""
    echo "Updating Homebrew..."
    brew update

    # Install Python 3
    if ! command_exists python3; then
        echo ""
        echo "Installing Python 3..."
        brew install python@3
    else
        print_status "Python 3 already installed ($(python3 --version))"
    fi

    # Install exiftool
    if ! command_exists exiftool; then
        echo ""
        echo "Installing exiftool..."
        brew install exiftool
    else
        print_status "exiftool already installed ($(exiftool -ver))"
    fi

    # Install ffmpeg (includes ffprobe)
    if ! command_exists ffprobe; then
        echo ""
        echo "Installing ffmpeg (includes ffprobe)..."
        brew install ffmpeg
    else
        print_status "ffmpeg/ffprobe already installed"
    fi

    # Install Docker (if not skipped)
    if [[ "$SKIP_DOCKER" == false ]]; then
        if ! command_exists docker; then
            echo ""
            print_warning "Docker not found"
            echo "Docker Desktop is required for AUPAT v0.1.2"
            echo "Please install from: https://www.docker.com/products/docker-desktop/"
            echo ""
            read -p "Press Enter after installing Docker Desktop..."
        else
            print_status "Docker already installed ($(docker --version))"
        fi

        # Check docker-compose
        if ! command_exists docker-compose && ! docker compose version &> /dev/null; then
            print_warning "docker-compose not found"
            echo "Docker Compose is included in Docker Desktop"
            echo "If you just installed Docker Desktop, restart your terminal"
        else
            print_status "docker-compose available"
        fi
    fi

    # Install Git
    if ! command_exists git; then
        echo ""
        echo "Installing Git..."
        brew install git
    else
        print_status "Git already installed ($(git --version))"
    fi
}

# Linux installation
install_linux() {
    echo "========================================="
    echo "Linux Installation"
    echo "========================================="
    echo ""

    case "$OS" in
        ubuntu|debian)
            echo "Detected Debian/Ubuntu"
            echo ""

            # Update package index
            echo "Updating package index..."
            sudo apt-get update

            # Install Python 3
            if ! command_exists python3; then
                echo ""
                echo "Installing Python 3..."
                sudo apt-get install -y python3 python3-venv python3-pip
            else
                print_status "Python 3 already installed ($(python3 --version))"
            fi

            # Install exiftool
            if ! command_exists exiftool; then
                echo ""
                echo "Installing exiftool..."
                sudo apt-get install -y libimage-exiftool-perl
            else
                print_status "exiftool already installed ($(exiftool -ver))"
            fi

            # Install ffmpeg
            if ! command_exists ffprobe; then
                echo ""
                echo "Installing ffmpeg..."
                sudo apt-get install -y ffmpeg
            else
                print_status "ffmpeg/ffprobe already installed"
            fi

            # Install Docker (if not skipped)
            if [[ "$SKIP_DOCKER" == false ]]; then
                if ! command_exists docker; then
                    echo ""
                    echo "Installing Docker..."
                    curl -fsSL https://get.docker.com -o get-docker.sh
                    sudo sh get-docker.sh
                    sudo usermod -aG docker "$USER"
                    rm get-docker.sh
                    print_warning "Docker installed. Log out and back in for group changes to take effect"
                else
                    print_status "Docker already installed ($(docker --version))"
                fi
            fi

            # Install Git
            if ! command_exists git; then
                echo ""
                echo "Installing Git..."
                sudo apt-get install -y git
            else
                print_status "Git already installed ($(git --version))"
            fi
            ;;

        fedora|rhel|centos)
            echo "Detected Fedora/RHEL/CentOS"
            echo ""
            print_warning "Fedora/RHEL installation not fully automated"
            echo "Please install manually:"
            echo "  sudo dnf install python3 perl-Image-ExifTool ffmpeg git docker"
            echo "  sudo systemctl start docker"
            echo "  sudo usermod -aG docker \$USER"
            ;;

        arch|manjaro)
            echo "Detected Arch Linux"
            echo ""
            print_warning "Arch Linux installation not fully automated"
            echo "Please install manually:"
            echo "  sudo pacman -S python python-pip perl-image-exiftool ffmpeg git docker"
            echo "  sudo systemctl start docker"
            echo "  sudo usermod -aG docker \$USER"
            ;;

        *)
            echo "Unsupported Linux distribution: $OS"
            echo ""
            echo "Please install manually:"
            echo "  - Python 3 (with pip and venv)"
            echo "  - exiftool (perl-Image-ExifTool)"
            echo "  - ffmpeg (includes ffprobe)"
            echo "  - Git"
            echo "  - Docker and Docker Compose"
            exit 1
            ;;
    esac
}

# Install based on OS
case "$OS" in
    macOS)
        install_macos
        ;;
    ubuntu|debian|fedora|rhel|centos|arch|manjaro)
        install_linux
        ;;
    *)
        print_error "Unsupported operating system: $OS"
        exit 1
        ;;
esac

# Python virtual environment setup
echo ""
echo "========================================="
echo "Python Environment Setup"
echo "========================================="
echo ""

# Create virtual environment if it doesn't exist
if [[ ! -d "venv" ]]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install Python dependencies
if [[ -f "requirements.txt" ]]; then
    echo ""
    echo "Installing Python dependencies from requirements.txt..."
    pip install -r requirements.txt
    print_status "Python dependencies installed"
else
    print_warning "requirements.txt not found"
fi

# Create user configuration if needed
echo ""
echo "========================================="
echo "Configuration Setup"
echo "========================================="
echo ""

if [[ ! -f "user/user.json" ]]; then
    if [[ -f "user/user.json.template" ]]; then
        echo "Creating user/user.json from template..."

        # Create user.json with absolute paths
        cat > user/user.json << EOF
{
  "db_name": "aupat.db",
  "db_loc": "${SCRIPT_DIR}/data",
  "db_backup": "${SCRIPT_DIR}/data/backups/",
  "db_ingest": "${SCRIPT_DIR}/data/ingest/",
  "arch_loc": "${SCRIPT_DIR}/data/archive/"
}
EOF
        print_status "user/user.json created with absolute paths"
    else
        print_warning "user/user.json.template not found"
    fi
else
    print_status "user/user.json already exists"
fi

# Create required directories
echo ""
echo "Creating required directories..."
mkdir -p data/archive
mkdir -p data/backups
mkdir -p data/ingest
mkdir -p logs
print_status "Directory structure created"

# Verify installation
echo ""
echo "========================================="
echo "Installation Verification"
echo "========================================="
echo ""

# Check Python
if command_exists python3; then
    print_status "Python 3: $(python3 --version)"
else
    print_error "Python 3 not found"
fi

# Check exiftool
if command_exists exiftool; then
    print_status "exiftool: version $(exiftool -ver)"
else
    print_error "exiftool not found"
fi

# Check ffprobe
if command_exists ffprobe; then
    print_status "ffprobe: available"
else
    print_error "ffprobe not found"
fi

# Check Docker (if not skipped)
if [[ "$SKIP_DOCKER" == false ]]; then
    if command_exists docker; then
        print_status "Docker: $(docker --version)"
    else
        print_error "Docker not found"
    fi

    if command_exists docker-compose || docker compose version &> /dev/null; then
        print_status "docker-compose: available"
    else
        print_error "docker-compose not found"
    fi
fi

# Check Git
if command_exists git; then
    print_status "Git: $(git --version)"
else
    print_error "Git not found"
fi

# Check virtual environment
if [[ -d "venv" ]]; then
    print_status "Python virtual environment: venv/"
else
    print_error "Virtual environment not found"
fi

# Check configuration
if [[ -f "user/user.json" ]]; then
    print_status "Configuration: user/user.json"
else
    print_warning "Configuration not found: user/user.json"
fi

echo ""
echo "========================================="
echo "Installation Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Run database migration:"
echo "   python scripts/db_migrate_v012.py"
echo ""
echo "3. Start Docker services:"
echo "   docker-compose up -d"
echo ""
echo "4. Check service health:"
echo "   docker-compose ps"
echo "   curl http://localhost:5000/api/health"
echo ""
echo "5. Run tests:"
echo "   pytest -v"
echo ""
echo "For more information, see docs/v0.1.2/README.md"
echo ""
