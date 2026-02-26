# Safari Font Rendering Issue - Technical Explanation

## The Problem

Safari on some Macs fails to render italic text correctly when using system fonts (`-apple-system`, `BlinkMacSystemFont`), displaying Chinese/Kanji characters or gibberish instead of English text.

## Why This Happens

### 1. **System Font Rendering in Safari**
- Safari handles system fonts differently than Chrome/Firefox
- The `-apple-system` font is actually San Francisco (SF Pro) on macOS
- Safari's font fallback mechanism for italic variants can fail
- When Safari can't find the italic variant of a system font, it may fall back to an incorrect font or character set

### 2. **Italic Font Variants**
- System fonts like `-apple-system` rely on the OS to provide font variants
- Italic variants may not be properly registered or accessible
- Safari's font matching algorithm can select the wrong font when the italic variant isn't available
- This can result in using a font with a different character encoding (e.g., a CJK font)

### 3. **Safari Version Differences**
- Older Safari versions (pre-14) had more font rendering bugs
- Safari 14+ improved font handling but still has quirks
- Different macOS versions bundle different system fonts
- Font availability varies by macOS version

### 4. **Character Encoding Issues**
- When Safari fails to find the correct italic font, it may:
  - Fall back to a font with different Unicode ranges
  - Use a font that doesn't support Latin characters properly
  - Render characters from a different script (CJK, Cyrillic, etc.)
- This explains why Chinese/Kanji characters appear

## Why Chrome Works

Chrome uses a different font rendering engine:
- Chrome's font fallback is more robust
- Chrome handles system font variants better
- Chrome has better error recovery when fonts fail
- Chrome's font matching algorithm is more forgiving

## The Solution

We fixed it by using explicit font names instead of system fonts:

**Before (broken in Safari):**
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
font-style: italic;
```

**After (works in Safari):**
```css
font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
font-style: italic;
```

### Why This Works

1. **Explicit Font Names**: Helvetica Neue, Helvetica, and Arial are always available on macOS
2. **Reliable Italic Variants**: These fonts have well-defined italic variants that Safari can find
3. **No System Font Dependency**: We're not relying on the OS to resolve system font names
4. **Cross-Browser Compatibility**: These fonts work in all browsers

## Factors That Could Affect This

### Safari Version
- **Safari 13 and earlier**: More likely to have this issue
- **Safari 14-16**: Improved but still can have issues
- **Safari 17+**: Better font handling, but system fonts can still be problematic

### macOS Version
- **macOS Big Sur (11.0)**: Changed system font to SF Pro, introduced some rendering issues
- **macOS Monterey (12.0)**: Improved font handling
- **macOS Ventura (13.0)**: Further improvements
- **macOS Sonoma (14.0)**: Latest improvements

### System Font Installation
- If system fonts are corrupted or missing
- If font caches are corrupted
- If custom fonts interfere with system fonts

### Font Preferences
- User's font smoothing preferences
- Display scaling settings
- Accessibility font size settings

## Questions to Ask Rosemary

1. **Safari Version**: What version of Safari? (Safari → About Safari)
2. **macOS Version**: What version of macOS? (Apple menu → About This Mac)
3. **Font Issues Elsewhere**: Does she see font issues in other websites?
4. **System Fonts**: Has she modified or removed any system fonts?
5. **Font Management Software**: Does she use any font management software that might interfere?

## Prevention

To avoid this issue in the future:
- Use explicit font names instead of system fonts for italic text
- Test in Safari, not just Chrome
- Consider using web fonts (Google Fonts, etc.) for critical text
- Avoid relying on system font variants for styled text

## References

- [Safari Font Rendering Issues](https://webkit.org/blog/3709/using-the-system-font-in-web-content/)
- [CSS Font Loading](https://developer.mozilla.org/en-US/docs/Web/CSS/@font-face)
- [Safari Font Fallback](https://developer.apple.com/design/human-interface-guidelines/typography)

