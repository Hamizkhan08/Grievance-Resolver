import React, { useState, useEffect } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet'
import { LatLng } from 'leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import './MapPicker.css'

// Fix for default marker icons in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

const MapClickHandler = ({ onLocationSelect }) => {
  useMapEvents({
    click: (e) => {
      const { lat, lng } = e.latlng
      onLocationSelect({ lat, lng })
    },
  })
  return null
}

const MapPicker = ({ onLocationSelect: externalOnLocationSelect }) => {
  const [selectedLocation, setSelectedLocation] = useState(null)
  const [mapCenter, setMapCenter] = useState([20.5937, 78.9629]) // India center
  const [locationName, setLocationName] = useState('')

  useEffect(() => {
    // Try to get user's location
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords
          setMapCenter([latitude, longitude])
        },
        () => {
          // Default to India center if geolocation fails
          console.log('Using default India center')
        }
      )
    }
  }, [])

  const handleLocationSelect = async ({ lat, lng }) => {
    setSelectedLocation({ lat, lng })
    
    // Reverse geocode to get address
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`
      )
      const data = await response.json()
      
      const address = data.address || {}
      const locationData = {
        lat,
        lng,
        address: data.display_name,
        state: address.state || '',
        city: address.city || address.town || address.village || '',
        district: address.county || '',
        pincode: address.postcode || '',
      }
      
      setLocationName(data.display_name)
      
      if (externalOnLocationSelect) {
        externalOnLocationSelect(locationData)
      }
    } catch (error) {
      console.error('Reverse geocoding failed:', error)
      setLocationName(`Lat: ${lat.toFixed(4)}, Lng: ${lng.toFixed(4)}`)
    }
  }

  return (
    <div className="map-picker">
      <h3>Select Location on Map</h3>
      <p className="map-instructions">
        Click on the map to select the exact location of your complaint
      </p>
      
      <div className="map-container">
        <MapContainer
          center={mapCenter}
          zoom={6}
          style={{ height: '400px', width: '100%', borderRadius: '0.5rem' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MapClickHandler onLocationSelect={handleLocationSelect} />
          {selectedLocation && (
            <Marker position={[selectedLocation.lat, selectedLocation.lng]}>
              <Popup>
                <div>
                  <strong>Selected Location</strong>
                  <br />
                  {locationName || `Lat: ${selectedLocation.lat.toFixed(4)}, Lng: ${selectedLocation.lng.toFixed(4)}`}
                </div>
              </Popup>
            </Marker>
          )}
        </MapContainer>
      </div>

      {selectedLocation && (
        <div className="selected-location-info">
          <strong>Selected:</strong> {locationName || 'Location selected'}
        </div>
      )}
    </div>
  )
}

export default MapPicker

