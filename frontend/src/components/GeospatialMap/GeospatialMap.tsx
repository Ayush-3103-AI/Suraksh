"use client";

import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "./geospatial-map.css";

interface GeospatialMapProps {
  onStateClick?: (stateName: string, stateData: any) => void;
  threatMarkers?: Array<{
    lon: number;
    lat: number;
    level: "critical" | "high" | "medium" | "low";
  }>;
}

export default function GeospatialMap({
  onStateClick,
  threatMarkers = [],
}: GeospatialMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const geoJsonLayerRef = useRef<L.GeoJSON | null>(null);
  const heatmapLayerRef = useRef<any>(null);
  const markersRef = useRef<L.Marker[]>([]);
  const [geoData, setGeoData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetch("/data/india-states.geojson")
      .then((response) => response.json())
      .then((data) => {
        setGeoData(data);
        setIsLoading(false);
      })
      .catch((error) => {
        console.error("Error loading GeoJSON data:", error);
        setIsLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!mapContainerRef.current || !geoData) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [27.0238, 74.2179] as L.LatLngExpression,
        zoom: 7,
        minZoom: 5,
        maxZoom: 19,
        zoomControl: true,
        scrollWheelZoom: true,
        doubleClickZoom: true,
        attributionControl: false,
      });

      const osmTileLayer = L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
          attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          maxZoom: 19,
        }
      );

      osmTileLayer.addTo(map);
      mapInstanceRef.current = map;
    }

    const map = mapInstanceRef.current;
    if (!map) return;

    if (geoJsonLayerRef.current) {
      map.removeLayer(geoJsonLayerRef.current);
    }

    const stateStyle = (feature: any) => {
      return {
        color: "transparent",
        weight: 0,
        fillOpacity: 0,
        fillColor: "transparent",
        opacity: 0,
      };
    };

    const onEachFeature = (feature: any, layer: L.Layer) => {
      const stateName = feature.properties.ST_NM || "Unknown";
      const isRajasthan =
        feature.properties.ST_NM === "Rajasthan" ||
        feature.properties.ST_CODE === "RJ";

      layer.on({
        mouseover: (e) => {
          const layer = e.target;
          layer.setStyle({
            weight: 0,
            fillOpacity: 0,
            color: "transparent",
            opacity: 0,
          });
          layer.bindTooltip(stateName, {
            permanent: false,
            direction: "top",
            className: "custom-tooltip",
          }).openTooltip();
        },
        mouseout: (e) => {
          geoJsonLayerRef.current?.resetStyle(e.target);
          e.target.closeTooltip();
        },
        click: () => {
          if (onStateClick) {
            onStateClick(stateName, feature.properties);
          }
        },
      });
    };

    const geoJsonLayer = L.geoJSON(geoData, {
      style: stateStyle,
      onEachFeature: onEachFeature,
    });

    geoJsonLayer.addTo(map);
    geoJsonLayerRef.current = geoJsonLayer;

    // Center on Rajasthan (already set in map initialization)
    // Initial view: center [27.0238, 74.2179], zoom 7

    return () => {
      if (geoJsonLayerRef.current) {
        map.removeLayer(geoJsonLayerRef.current);
      }
    };
  }, [geoData, onStateClick]);

  useEffect(() => {
    if (!mapInstanceRef.current || !geoData) return;

    const map = mapInstanceRef.current;

    // Remove existing heatmap layer if present
    if (heatmapLayerRef.current) {
      map.removeLayer(heatmapLayerRef.current);
      heatmapLayerRef.current = null;
    }
  }, [threatMarkers, geoData]);

  useEffect(() => {
    if (!mapInstanceRef.current || !geoData) return;

    markersRef.current.forEach((marker) => {
      mapInstanceRef.current?.removeLayer(marker);
    });
    markersRef.current = [];

    const threatColors = {
      critical: "#FF0055",
      high: "#FF6B00",
      medium: "#FFB800",
      low: "#00FF88",
    };

    threatMarkers.forEach((marker) => {
      const customIcon = L.divIcon({
        className: "threat-marker",
        html: `<div style="
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background-color: ${threatColors[marker.level]};
          box-shadow: 0 0 20px ${threatColors[marker.level]};
          animation: pulse 2s ease-in-out infinite;
        "></div>`,
        iconSize: [16, 16],
        iconAnchor: [8, 8],
      });

      const leafletMarker = L.marker([marker.lat, marker.lon], {
        icon: customIcon,
      }).addTo(mapInstanceRef.current!);

      leafletMarker.bindTooltip(
        `Threat Level: ${marker.level.toUpperCase()}`,
        {
          permanent: false,
          direction: "top",
          className: "threat-tooltip",
        }
      );

      markersRef.current.push(leafletMarker);
    });
  }, [threatMarkers, geoData]);

  useEffect(() => {
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  if (isLoading) {
    return (
      <div className="h-full w-full flex items-center justify-center bg-gradient-to-br from-space-100 to-space-200">
        <div className="text-cyan-400 text-sm">Loading map data...</div>
      </div>
    );
  }

  return (
    <div
      ref={mapContainerRef}
      className="h-full w-full geospatial-map-container"
      style={{ minHeight: "400px" }}
    />
  );
}

