import 'dart:io';
import 'dart:convert';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as path;
import 'package:uuid/uuid.dart';

/// Service for capturing and managing photos for locations
///
/// Features:
/// - Camera capture with compression
/// - Gallery photo selection
/// - Local storage management
/// - Base64 encoding for sync
class CameraService {
  final ImagePicker _picker = ImagePicker();
  final Uuid _uuid = const Uuid();

  /// Capture photo from camera
  /// Returns File path if successful, null if cancelled
  Future<File?> capturePhoto() async {
    try {
      final XFile? photo = await _picker.pickImage(
        source: ImageSource.camera,
        maxWidth: 1920,  // HD resolution
        maxHeight: 1080,
        imageQuality: 85,  // Balance quality and size
      );

      if (photo == null) return null;

      // Save to app directory with unique name
      final savedFile = await _saveToAppDirectory(File(photo.path));
      return savedFile;
    } catch (e) {
      print('Error capturing photo: $e');
      return null;
    }
  }

  /// Pick photo from gallery
  /// Returns File path if successful, null if cancelled
  Future<File?> pickFromGallery() async {
    try {
      final XFile? photo = await _picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 1920,
        maxHeight: 1080,
        imageQuality: 85,
      );

      if (photo == null) return null;

      // Save to app directory
      final savedFile = await _saveToAppDirectory(File(photo.path));
      return savedFile;
    } catch (e) {
      print('Error picking photo: $e');
      return null;
    }
  }

  /// Pick multiple photos from gallery
  /// Returns list of File paths
  Future<List<File>> pickMultipleFromGallery() async {
    try {
      final List<XFile> photos = await _picker.pickMultipleImages(
        maxWidth: 1920,
        maxHeight: 1080,
        imageQuality: 85,
      );

      final List<File> savedFiles = [];
      for (final photo in photos) {
        final savedFile = await _saveToAppDirectory(File(photo.path));
        savedFiles.add(savedFile);
      }

      return savedFiles;
    } catch (e) {
      print('Error picking multiple photos: $e');
      return [];
    }
  }

  /// Save temporary file to app directory with unique name
  Future<File> _saveToAppDirectory(File tempFile) async {
    final appDir = await getApplicationDocumentsDirectory();
    final photosDir = Directory(path.join(appDir.path, 'photos'));

    // Create photos directory if it doesn't exist
    if (!await photosDir.exists()) {
      await photosDir.create(recursive: true);
    }

    // Generate unique filename
    final extension = path.extension(tempFile.path);
    final filename = '${_uuid.v4()}$extension';
    final newPath = path.join(photosDir.path, filename);

    // Copy file to app directory
    final newFile = await tempFile.copy(newPath);

    return newFile;
  }

  /// Convert photo to base64 for API upload
  Future<String> fileToBase64(File file) async {
    try {
      final bytes = await file.readAsBytes();
      return base64Encode(bytes);
    } catch (e) {
      print('Error encoding file to base64: $e');
      rethrow;
    }
  }

  /// Get file size in bytes
  Future<int> getFileSize(File file) async {
    try {
      return await file.length();
    } catch (e) {
      print('Error getting file size: $e');
      return 0;
    }
  }

  /// Delete photo file
  Future<bool> deletePhoto(String filePath) async {
    try {
      final file = File(filePath);
      if (await file.exists()) {
        await file.delete();
        return true;
      }
      return false;
    } catch (e) {
      print('Error deleting photo: $e');
      return false;
    }
  }

  /// Delete multiple photos
  Future<void> deletePhotos(List<String> filePaths) async {
    for (final filePath in filePaths) {
      await deletePhoto(filePath);
    }
  }

  /// Get total size of photos in bytes
  Future<int> getTotalPhotosSize(List<String> filePaths) async {
    int totalSize = 0;
    for (final filePath in filePaths) {
      final file = File(filePath);
      if (await file.exists()) {
        totalSize += await getFileSize(file);
      }
    }
    return totalSize;
  }

  /// Format file size for display (e.g., "2.5 MB")
  String formatFileSize(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  /// Clean up orphaned photos (photos not associated with any location)
  /// This should be called periodically to free up storage
  Future<int> cleanupOrphanedPhotos(List<String> activePhotoPaths) async {
    try {
      final appDir = await getApplicationDocumentsDirectory();
      final photosDir = Directory(path.join(appDir.path, 'photos'));

      if (!await photosDir.exists()) return 0;

      int deletedCount = 0;
      final files = await photosDir.list().toList();

      for (final entity in files) {
        if (entity is File) {
          final filePath = entity.path;
          // Delete if not in active photos list
          if (!activePhotoPaths.contains(filePath)) {
            await entity.delete();
            deletedCount++;
          }
        }
      }

      return deletedCount;
    } catch (e) {
      print('Error cleaning up orphaned photos: $e');
      return 0;
    }
  }
}
