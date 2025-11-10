# Homebrew formula for yourdad (Dad Ware)
# Install with: brew install --build-from-source ./Formula/yourdad.rb
# Or add to a tap for easier installation

class Yourdad < Formula
  desc "Dad Ware - A personality-driven Mac cleanup tool"
  homepage "https://github.com/yourusername/dadware"
  url "https://github.com/yourusername/dadware/archive/v0.1.0.tar.gz"
  sha256 "" # Update with actual SHA256 when releasing
  version "0.1.0"

  depends_on "python@3.9"

  def install
    # Install Python dependencies (if any)
    system "python3", "-m", "pip", "install", "--user", "--break-system-packages", "-r", "requirements.txt" if File.exist?("requirements.txt")
    
    # Install the main script
    bin.install "yourdad.py" => "yourdad"
    
    # Install supporting modules
    libexec.install Dir["personality", "renderers", "scanners", "utils"]
    
    # Make script executable
    chmod 0755, bin/"yourdad"
    
    # Create wrapper script that sets PYTHONPATH
    (bin/"yourdad").write <<~EOS
      #!/bin/bash
      export PYTHONPATH="#{libexec}:$PYTHONPATH"
      exec python3 "#{libexec}/../yourdad.py" "$@"
    EOS
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
    puts "Check permissions with: python3 scripts/check_permissions.py"
  end

  test do
    system "#{bin}/yourdad", "--version"
  end
end

