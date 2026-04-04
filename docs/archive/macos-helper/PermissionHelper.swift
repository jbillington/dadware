//
// PermissionHelper.swift
// macOS Helper for Full Disk Access Permission Management
//
// This Swift helper can be used by a Mac app bundle to check and request
// Full Disk Access permissions. CLI apps can optionally use this if bundled.
//

import Foundation
import AppKit

class PermissionHelper {
    
    /// Check if Full Disk Access is granted by testing access to protected directories
    static func checkFullDiskAccess() -> Bool {
        let testPaths = [
            FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Messages"),
            FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Mail"),
            FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Pictures/Photos Library.photoslibrary")
        ]
        
        for path in testPaths {
            if FileManager.default.fileExists(atPath: path.path) {
                do {
                    _ = try FileManager.default.contentsOfDirectory(atPath: path.path)
                } catch {
                    // If we can't read the directory, Full Disk Access is not granted
                    return false
                }
            }
        }
        
        return true
    }
    
    /// Open System Settings to the Full Disk Access page
    static func openSystemPreferences() {
        if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles") {
            NSWorkspace.shared.open(url)
        }
    }
    
    /// Request Full Disk Access (triggers system dialog if not granted)
    /// Note: This only works from a Mac app bundle, not from CLI
    static func requestFullDiskAccess() -> Bool {
        // This will trigger the system permission dialog automatically
        // when the app tries to access protected directories
        return checkFullDiskAccess()
    }
    
    /// Get detailed permission status for each protected directory
    static func getDetailedPermissionStatus() -> [String: Bool] {
        var status: [String: Bool] = [:]
        
        let messagesPath = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Messages")
        let mailPath = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Mail")
        let photosPath = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Pictures/Photos Library.photoslibrary")
        
        status["messages"] = canAccess(path: messagesPath)
        status["mail"] = canAccess(path: mailPath)
        status["photos"] = canAccess(path: photosPath)
        
        return status
    }
    
    private static func canAccess(path: URL) -> Bool {
        guard FileManager.default.fileExists(atPath: path.path) else {
            return false // Path doesn't exist, not a permission issue
        }
        
        do {
            _ = try FileManager.default.contentsOfDirectory(atPath: path.path)
            return true
        } catch {
            return false
        }
    }
}

