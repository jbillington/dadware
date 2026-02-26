# Homebrew formula for yourdad (Dad Ware)
# Install with: brew install --build-from-source ./Formula/yourdad.rb
# Or add to a tap for easier installation

class Yourdad < Formula
  desc "Dad Ware - A personality-driven Mac cleanup tool"
  homepage "https://github.com/yourusername/dadware"
  # For local development/testing, use file:// URL
  # For releases, use GitHub release URL
  url "file://#{Dir.pwd}"
  version "0.1.0"
  license "MIT"

  # Use system Python (macOS comes with Python 3.9+)
  # No need to depend on python@3.9 since we use system Python
  # depends_on "python@3.9"

  def install
    # Use system Python explicitly to avoid QGIS conflicts
    python3 = "/usr/bin/python3"
    
    # Verify Python is available
    unless File.exist?(python3)
      odie "System Python not found at #{python3}. Please install Python 3.9+."
    end
    
    # Install supporting modules to libexec
    libexec.install Dir["personality", "renderers", "scanners", "utils"]
    
    # Install the main script to bin
    bin.install "yourdad.py"
    
    # Create wrapper script that sets PYTHONPATH and uses system Python
    (bin/"yourdad").write <<~EOS
      #!/bin/bash
      export PYTHONPATH="#{libexec}:$PYTHONPATH"
      exec #{python3} "#{bin}/yourdad.py" "$@"
    EOS
    
    # Make wrapper executable
    chmod 0755, bin/"yourdad"
  end

  def post_install
    ohai "Installation complete!"
    puts ""
    puts "⚠️  IMPORTANT: Full Disk Access Required"
    puts ""
    puts "To scan Photos, Messages, and Mail libraries, you need to grant"
    puts "Full Disk Access to Terminal (or your IDE):"
    puts ""
    puts "  1. Open System Settings → Privacy & Security"
    puts "  2. Scroll to 'Full Disk Access'"
    puts "  3. Add Terminal.app (or your IDE)"
    puts "  4. Restart Terminal/IDE"
    puts ""
    puts "Run 'yourdad scan storage' to get started!"
    puts ""
    puts "Check permissions with: yourdad --help"
  end

  test do
    system "#{bin}/yourdad", "--version"
  end
end

