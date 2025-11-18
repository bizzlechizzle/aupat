import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';
import 'package:aupat_mobile/services/database_service.dart';
import 'package:aupat_mobile/services/gps_service.dart';
import 'package:aupat_mobile/services/camera_service.dart';
import 'package:aupat_mobile/models/location_model.dart';

/// Add location screen with GPS capture
/// Captures device GPS and creates new location
class AddLocationScreen extends StatefulWidget {
  const AddLocationScreen({super.key});

  @override
  State<AddLocationScreen> createState() => _AddLocationScreenState();
}

class _AddLocationScreenState extends State<AddLocationScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _uuid = const Uuid();
  final _cameraService = CameraService();

  String _selectedType = 'factory';
  final List<String> _locationTypes = [
    'factory',
    'mill',
    'church',
    'school',
    'hospital',
    'house',
    'commercial',
    'other',
  ];

  // Track captured photos
  List<File> _photos = [];

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _captureGps() async {
    final gpsService = Provider.of<GpsService>(context, listen: false);
    await gpsService.getCurrentPosition();
  }

  Future<void> _capturePhoto() async {
    final file = await _cameraService.capturePhoto();
    if (file != null) {
      setState(() {
        _photos.add(file);
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Photo captured (${_photos.length})'),
            backgroundColor: Colors.green,
            duration: const Duration(seconds: 1),
          ),
        );
      }
    }
  }

  Future<void> _pickFromGallery() async {
    final files = await _cameraService.pickMultipleFromGallery();
    if (files.isNotEmpty) {
      setState(() {
        _photos.addAll(files);
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('${files.length} photo(s) added'),
            backgroundColor: Colors.green,
            duration: const Duration(seconds: 1),
          ),
        );
      }
    }
  }

  void _removePhoto(int index) {
    setState(() {
      _photos.removeAt(index);
    });
  }

  Future<void> _saveLocation() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    final gpsService = Provider.of<GpsService>(context, listen: false);
    final position = gpsService.currentPosition;

    if (position == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please capture GPS coordinates first'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    // Create pending sync location with photo paths
    final pendingLocation = PendingSyncLocation(
      locUuid: _uuid.v4(),
      locName: _nameController.text,
      lat: position.latitude,
      lon: position.longitude,
      locType: _selectedType,
      photos: _photos.map((f) => f.path).toList(),
      createdAt: DateTime.now().toIso8601String(),
      syncAttempts: 0,
    );

    // Save to pending sync queue
    final dbService = Provider.of<DatabaseService>(context, listen: false);
    await dbService.addPendingSync(pendingLocation);

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Location saved! Will sync when on WiFi.'),
          backgroundColor: Colors.green,
        ),
      );

      // Clear form
      _nameController.clear();
      gpsService.clearPosition();
      setState(() {
        _selectedType = 'factory';
        _photos = [];
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Location name
            TextFormField(
              controller: _nameController,
              decoration: const InputDecoration(
                labelText: 'Location Name',
                hintText: 'e.g., Abandoned Factory A',
                border: OutlineInputBorder(),
              ),
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return 'Please enter a location name';
                }
                return null;
              },
            ),

            const SizedBox(height: 16),

            // Location type dropdown
            DropdownButtonFormField<String>(
              value: _selectedType,
              decoration: const InputDecoration(
                labelText: 'Location Type',
                border: OutlineInputBorder(),
              ),
              items: _locationTypes.map((type) {
                return DropdownMenuItem(
                  value: type,
                  child: Text(type[0].toUpperCase() + type.substring(1)),
                );
              }).toList(),
              onChanged: (value) {
                setState(() {
                  _selectedType = value!;
                });
              },
            ),

            const SizedBox(height: 24),

            // GPS capture section
            Consumer<GpsService>(
              builder: (context, gpsService, child) {
                return Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Text(
                          'GPS Coordinates',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 8),

                        if (gpsService.currentPosition != null) ...[
                          Text(
                            'Latitude: ${gpsService.currentPosition!.latitude.toStringAsFixed(6)}',
                          ),
                          Text(
                            'Longitude: ${gpsService.currentPosition!.longitude.toStringAsFixed(6)}',
                          ),
                          Text(
                            'Accuracy: ${gpsService.currentPosition!.accuracy.toStringAsFixed(1)}m',
                            style: TextStyle(
                              color: gpsService.isAccuracyAcceptable()
                                  ? Colors.green
                                  : Colors.orange,
                            ),
                          ),
                          if (gpsService.currentAddress != null)
                            Text('Address: ${gpsService.currentAddress}'),
                        ] else ...[
                          const Text('No GPS coordinates captured'),
                        ],

                        const SizedBox(height: 12),

                        if (gpsService.error != null)
                          Text(
                            gpsService.error!,
                            style: const TextStyle(color: Colors.red),
                          ),

                        ElevatedButton.icon(
                          onPressed: gpsService.isLoading ? null : _captureGps,
                          icon: gpsService.isLoading
                              ? const SizedBox(
                                  width: 16,
                                  height: 16,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                )
                              : const Icon(Icons.gps_fixed),
                          label: Text(
                            gpsService.isLoading ? 'Capturing GPS...' : 'Capture GPS',
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),

            const SizedBox(height: 24),

            // Photos section
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      'Photos (${_photos.length})',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),

                    // Photo grid
                    if (_photos.isNotEmpty)
                      GridView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: 3,
                          crossAxisSpacing: 8,
                          mainAxisSpacing: 8,
                        ),
                        itemCount: _photos.length,
                        itemBuilder: (context, index) {
                          return Stack(
                            fit: StackFit.expand,
                            children: [
                              ClipRRect(
                                borderRadius: BorderRadius.circular(8),
                                child: Image.file(
                                  _photos[index],
                                  fit: BoxFit.cover,
                                ),
                              ),
                              Positioned(
                                top: 4,
                                right: 4,
                                child: IconButton(
                                  icon: const Icon(Icons.close),
                                  onPressed: () => _removePhoto(index),
                                  style: IconButton.styleFrom(
                                    backgroundColor: Colors.black54,
                                    foregroundColor: Colors.white,
                                    padding: EdgeInsets.zero,
                                    minimumSize: const Size(32, 32),
                                  ),
                                ),
                              ),
                            ],
                          );
                        },
                      ),

                    if (_photos.isNotEmpty) const SizedBox(height: 12),

                    // Camera/Gallery buttons
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: _capturePhoto,
                            icon: const Icon(Icons.camera_alt),
                            label: const Text('Camera'),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: _pickFromGallery,
                            icon: const Icon(Icons.photo_library),
                            label: const Text('Gallery'),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 24),

            // Save button
            FilledButton.icon(
              onPressed: _saveLocation,
              icon: const Icon(Icons.save),
              label: const Text('Save Location'),
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.all(16),
              ),
            ),

            const SizedBox(height: 8),

            Text(
              'Note: Location will be synced to desktop when connected to WiFi',
              style: Theme.of(context).textTheme.bodySmall,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
