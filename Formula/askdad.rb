# Homebrew formula for the Ask Dad command-line tool.
#
# The published copy lives in the tap repo jbillington/homebrew-tap, so users run:
#   brew install jbillington/tap/askdad
#
# This file is the source. scripts/package_cli.sh rewrites the url, sha256 and
# version lines for each release; copy the result to the tap repo's Formula/.
# It installs the same signed, notarized universal binary as install.sh.

class Askdad < Formula
  desc "Read-only Mac storage and memory check-up, with a dad's advice"
  homepage "https://justaskdad.app"
  url "https://github.com/jbillington/dadware/releases/download/v1.0-beta/askdad-macos.tar.gz"
  sha256 "REPLACE_WITH_SHA256_FROM_PACKAGE_CLI"
  version "1.0-beta"
  license "MIT"

  depends_on :macos

  def install
    bin.install "askdad"
  end

  def caveats
    <<~EOS
      For the full report (Photos, Mail, Messages), give your terminal app
      Full Disk Access:
        System Settings > Privacy & Security > Full Disk Access
      The scan works without it; those libraries are skipped and labeled.
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/askdad --version")
  end
end
