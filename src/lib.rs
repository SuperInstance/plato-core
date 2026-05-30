use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Standardized tile identifier across the PLATO ecosystem
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct TileId(Uuid);

impl TileId {
    pub fn new() -> Self {
        Self(Uuid::new_v4())
    }

    pub fn as_uuid(&self) -> &Uuid {
        &self.0
    }
}

impl Default for TileId {
    fn default() -> Self {
        Self::new()
    }
}

/// Standardized embedding
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Embedding {
    pub id: TileId,
    pub vector: Vec<f64>,
    pub timestamp: u64,
    pub source: String,
}

impl Embedding {
    pub fn new(vector: Vec<f64>, source: &str) -> Self {
        Self {
            id: TileId::new(),
            vector,
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or_default()
                .as_secs(),
            source: source.to_string(),
        }
    }

    pub fn cosine_similarity(&self, other: &Embedding) -> f64 {
        if self.vector.len() != other.vector.len() || self.vector.is_empty() {
            return 0.0;
        }
        let dot: f64 = self.vector.iter().zip(&other.vector).map(|(a, b)| a * b).sum();
        let mag_a: f64 = self.vector.iter().map(|v| v * v).sum::<f64>().sqrt();
        let mag_b: f64 = other.vector.iter().map(|v| v * v).sum::<f64>().sqrt();
        if mag_a == 0.0 || mag_b == 0.0 {
            return 0.0;
        }
        dot / (mag_a * mag_b)
    }

    pub fn euclidean_distance(&self, other: &Embedding) -> f64 {
        if self.vector.len() != other.vector.len() {
            return f64::INFINITY;
        }
        self.vector
            .iter()
            .zip(&other.vector)
            .map(|(a, b)| (a - b).powi(2))
            .sum::<f64>()
            .sqrt()
    }
}

/// Standardized room identifier
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct RoomId(Uuid);

impl RoomId {
    pub fn new() -> Self {
        Self(Uuid::new_v4())
    }

    pub fn as_uuid(&self) -> &Uuid {
        &self.0
    }
}

impl Default for RoomId {
    fn default() -> Self {
        Self::new()
    }
}

/// Standardized signal types
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum SignalType {
    Vibe,
    Surprise,
    Murmur,
    Alert,
    Heartbeat,
}

/// Standardized timestamp
pub type Tick = u64;

/// Confidence value [0.0, 1.0]
pub type Confidence = f64;

/// Health status for any PLATO component
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum HealthStatus {
    Healthy,
    Degraded { reason: String },
    Failed { reason: String },
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- TileId tests ---

    #[test]
    fn test_tile_id_generation() {
        let id = TileId::new();
        assert!(!id.as_uuid().is_nil());
    }

    #[test]
    fn test_tile_id_uniqueness() {
        let a = TileId::new();
        let b = TileId::new();
        assert_ne!(a, b);
    }

    #[test]
    fn test_tile_id_serialization_roundtrip() {
        let id = TileId::new();
        let json = serde_json::to_string(&id).unwrap();
        let deserialized: TileId = serde_json::from_str(&json).unwrap();
        assert_eq!(id, deserialized);
    }

    #[test]
    fn test_tile_id_equality() {
        let id = TileId::new();
        assert_eq!(id, id.clone());
    }

    #[test]
    fn test_tile_id_hash() {
        use std::collections::HashSet;
        let mut set = HashSet::new();
        let id = TileId::new();
        set.insert(id.clone());
        assert!(set.contains(&id));
    }

    // --- Embedding tests ---

    #[test]
    fn test_embedding_creation() {
        let e = Embedding::new(vec![1.0, 2.0, 3.0], "test");
        assert_eq!(e.vector, vec![1.0, 2.0, 3.0]);
        assert_eq!(e.source, "test");
    }

    #[test]
    fn test_cosine_identical_vectors() {
        let a = Embedding::new(vec![1.0, 0.0, 0.0], "a");
        let b = Embedding::new(vec![1.0, 0.0, 0.0], "b");
        let sim = a.cosine_similarity(&b);
        assert!((sim - 1.0).abs() < 1e-9);
    }

    #[test]
    fn test_cosine_orthogonal_vectors() {
        let a = Embedding::new(vec![1.0, 0.0], "a");
        let b = Embedding::new(vec![0.0, 1.0], "b");
        let sim = a.cosine_similarity(&b);
        assert!(sim.abs() < 1e-9);
    }

    #[test]
    fn test_euclidean_distance() {
        let a = Embedding::new(vec![0.0, 0.0], "a");
        let b = Embedding::new(vec![3.0, 4.0], "b");
        let dist = a.euclidean_distance(&b);
        assert!((dist - 5.0).abs() < 1e-9);
    }

    #[test]
    fn test_embedding_empty_vector() {
        let e = Embedding::new(vec![], "empty");
        assert!(e.vector.is_empty());
        let other = Embedding::new(vec![], "empty2");
        assert_eq!(e.cosine_similarity(&other), 0.0);
    }

    #[test]
    fn test_embedding_different_lengths() {
        let a = Embedding::new(vec![1.0, 2.0], "a");
        let b = Embedding::new(vec![1.0], "b");
        assert!(a.euclidean_distance(&b).is_infinite());
        assert_eq!(a.cosine_similarity(&b), 0.0);
    }

    // --- RoomId tests ---

    #[test]
    fn test_room_id_generation() {
        let id = RoomId::new();
        assert!(!id.as_uuid().is_nil());
    }

    #[test]
    fn test_room_id_equality_and_hash() {
        use std::collections::HashSet;
        let a = RoomId::new();
        let b = RoomId::new();
        assert_eq!(a, a.clone());
        assert_ne!(a, b);
        let mut set = HashSet::new();
        set.insert(a.clone());
        assert!(set.contains(&a));
        assert!(!set.contains(&b));
    }

    #[test]
    fn test_room_id_serialization() {
        let id = RoomId::new();
        let json = serde_json::to_string(&id).unwrap();
        let back: RoomId = serde_json::from_str(&json).unwrap();
        assert_eq!(id, back);
    }

    // --- SignalType tests ---

    #[test]
    fn test_signal_type_variants() {
        let variants = vec![
            SignalType::Vibe,
            SignalType::Surprise,
            SignalType::Murmur,
            SignalType::Alert,
            SignalType::Heartbeat,
        ];
        for v in &variants {
            let json = serde_json::to_string(v).unwrap();
            let back: SignalType = serde_json::from_str(&json).unwrap();
            assert_eq!(*v, back);
        }
    }

    #[test]
    fn test_signal_type_distinct() {
        assert_ne!(SignalType::Vibe, SignalType::Alert);
        assert_ne!(SignalType::Murmur, SignalType::Heartbeat);
    }

    // --- Tick and Confidence type tests ---

    #[test]
    fn test_tick_type() {
        let t: Tick = 12345u64;
        assert_eq!(t, 12345u64);
    }

    #[test]
    fn test_confidence_type() {
        let c: Confidence = 0.95;
        assert!((c - 0.95).abs() < f64::EPSILON);
    }

    // --- HealthStatus tests ---

    #[test]
    fn test_health_status_variants() {
        let healthy = HealthStatus::Healthy;
        let degraded = HealthStatus::Degraded {
            reason: "slow".into(),
        };
        let failed = HealthStatus::Failed {
            reason: "crash".into(),
        };
        assert_ne!(healthy, degraded);
        assert_ne!(degraded, failed);
    }

    #[test]
    fn test_health_status_serialization() {
        let status = HealthStatus::Degraded {
            reason: "high load".into(),
        };
        let json = serde_json::to_string(&status).unwrap();
        let back: HealthStatus = serde_json::from_str(&json).unwrap();
        assert_eq!(status, back);
    }

    // --- Send+Sync tests ---

    fn assert_send_sync<T: Send + Sync>() {}

    #[test]
    fn test_send_sync() {
        assert_send_sync::<TileId>();
        assert_send_sync::<RoomId>();
        assert_send_sync::<Embedding>();
        assert_send_sync::<SignalType>();
        assert_send_sync::<HealthStatus>();
    }

    // --- Debug + Clone for all ---

    #[test]
    fn test_debug_clone() {
        let tid = TileId::new();
        assert!(!format!("{:?}", tid).is_empty());
        assert_eq!(tid, tid.clone());

        let rid = RoomId::new();
        assert!(!format!("{:?}", rid).is_empty());
        assert_eq!(rid, rid.clone());

        let e = Embedding::new(vec![1.0], "test");
        assert!(!format!("{:?}", e).is_empty());
        assert_eq!(e.vector, e.clone().vector);

        let s = SignalType::Vibe;
        assert_eq!(s, s.clone());

        let h = HealthStatus::Healthy;
        assert_eq!(h, h.clone());
    }

    // --- Embedding source/timestamp ---

    #[test]
    fn test_embedding_source_and_timestamp() {
        let e = Embedding::new(vec![1.0], "source-name");
        assert_eq!(e.source, "source-name");
        assert!(e.timestamp > 0);
    }

    // --- Multiple TileIds differ ---

    #[test]
    fn test_multiple_tile_ids_differ() {
        let ids: Vec<TileId> = (0..100).map(|_| TileId::new()).collect();
        let unique: std::collections::HashSet<TileId> = ids.into_iter().collect();
        assert_eq!(unique.len(), 100);
    }

    // --- Dimension tests ---

    #[test]
    fn test_single_dim_embedding() {
        let a = Embedding::new(vec![1.0], "a");
        let b = Embedding::new(vec![-1.0], "b");
        assert!((a.cosine_similarity(&b) - (-1.0)).abs() < 1e-9);
    }

    #[test]
    fn test_1000_dim_embedding() {
        let v: Vec<f64> = (0..1000).map(|i| (i as f64).sin()).collect();
        let e = Embedding::new(v.clone(), "big");
        assert_eq!(e.vector.len(), 1000);
        let sim = e.cosine_similarity(&Embedding::new(v.clone(), "big2"));
        assert!((sim - 1.0).abs() < 1e-6);
    }

    #[test]
    fn test_empty_source() {
        let e = Embedding::new(vec![1.0], "");
        assert!(e.source.is_empty());
    }

    #[test]
    fn test_zero_timestamp_possible() {
        let mut e = Embedding::new(vec![1.0], "test");
        e.timestamp = 0;
        assert_eq!(e.timestamp, 0);
    }

    #[test]
    fn test_negative_embedding_values() {
        let a = Embedding::new(vec![-1.0, -2.0, -3.0], "neg");
        let b = Embedding::new(vec![-1.0, -2.0, -3.0], "neg2");
        assert!((a.cosine_similarity(&b) - 1.0).abs() < 1e-9);
        assert!((a.euclidean_distance(&b)).abs() < 1e-9);
    }
}
