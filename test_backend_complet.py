#!/usr/bin/env python3
"""
Test Backend Complet - Trend & Viral Engine Pro
Vérifie tous les endpoints et fonctionnalités critiques
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from src.api.main import app
from fastapi.testclient import TestClient

def test_backend():
    """Test complet du backend."""
    
    print("=" * 80)
    print("🧪 TESTS BACKEND COMPLET - Trend & Viral Engine Pro")
    print("=" * 80)
    print()
    
    client = TestClient(app)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Health Check
    tests_total += 1
    print(f"Test {tests_total}: Health Check")
    print("-" * 40)
    try:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✅ PASS - Status: {data['status']}, Version: {data['version']}")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL - {e}")
    print()
    
    # Test 2: Stats Overview (NOUVEAU)
    tests_total += 1
    print(f"Test {tests_total}: Stats Overview (NOUVEAU ENDPOINT)")
    print("-" * 40)
    try:
        response = client.get("/api/v1/stats/overview")
        assert response.status_code == 200
        data = response.json()
        assert "trends_collected" in data
        assert "predictions_made" in data
        assert "videos_generated" in data
        assert "model_accuracy" in data
        print(f"✅ PASS - Trends: {data['trends_collected']}, "
              f"Predictions: {data['predictions_made']}, "
              f"Videos: {data['videos_generated']}, "
              f"Accuracy: {data['model_accuracy']:.1%}")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL - {e}")
    print()
    
    # Test 3: Predict avec projection_7_days
    tests_total += 1
    print(f"Test {tests_total}: Predict avec projection_7_days (FIX CRITIQUE)")
    print("-" * 40)
    try:
        response = client.post("/api/v1/predict", json={
            "title": "Amazing AI Demo 2025",
            "platform": "tiktok",
            "follower_count": 100000
        })
        assert response.status_code == 200
        data = response.json()
        assert "projection_7_days" in data
        assert len(data["projection_7_days"]) == 7
        assert "viral_probability" in data
        print(f"✅ PASS - Views: {data['predicted_views']:,}, "
              f"Viral: {data['viral_probability']:.1%}, "
              f"Projection: {len(data['projection_7_days'])} jours")
        print(f"   Jour 1: {data['projection_7_days'][0]['views']:,} vues")
        print(f"   Jour 7: {data['projection_7_days'][-1]['views']:,} vues")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL - {e}")
    print()
    
    # Test 4: Trends TopK
    tests_total += 1
    print(f"Test {tests_total}: Trends TopK")
    print("-" * 40)
    try:
        response = client.get("/api/v1/trends/topK?k=5")
        assert response.status_code == 200
        data = response.json()
        assert "trends" in data
        assert data["count"] == 5
        print(f"✅ PASS - Count: {data['count']}, Country: {data.get('country', 'N/A')}")
        if data["trends"]:
            print(f"   Top trend: {data['trends'][0]['topic']} (score: {data['trends'][0]['score']:.2f})")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL - {e}")
    print()
    
    # Test 5: Generate Script
    tests_total += 1
    print(f"Test {tests_total}: Generate Script")
    print("-" * 40)
    try:
        response = client.post("/api/v1/generate/script", params={
            "topic": "AI Revolution 2025",
            "platform": "youtube",
            "duration": 120
        })
        assert response.status_code == 200
        data = response.json()
        assert "script" in data
        assert len(data["script"]) > 100
        print(f"✅ PASS - Script: {len(data['script'])} chars, "
              f"Platform: {data['platform']}, Duration: {data['duration']}s")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL - {e}")
    print()
    
    # Test 6: Analyze Post (NOUVEAU)
    tests_total += 1
    print(f"Test {tests_total}: Analyze Post (NOUVEAU ENDPOINT)")
    print("-" * 40)
    try:
        response = client.post("/api/v1/analyze-post", json={
            "url": "https://www.tiktok.com/@test/video/123456",
            "extract_content": False
        })
        assert response.status_code == 200
        data = response.json()
        assert "platform" in data
        assert "analysis" in data
        assert data["platform"] == "tiktok"
        print(f"✅ PASS - Platform: {data['platform']}, "
              f"Analysis keys: {len(data['analysis'])} items")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL - {e}")
    print()
    
    # Test 7: Static Files Mounting
    tests_total += 1
    print(f"Test {tests_total}: Static Files Mounting (FIX CRITIQUE)")
    print("-" * 40)
    try:
        # Vérifier que le mount existe dans l'app
        routes = [route.path for route in app.routes]
        assert any("/outputs" in route for route in routes)
        print(f"✅ PASS - StaticFiles monté sur /outputs")
        print(f"   Routes disponibles: {len(routes)} total")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL - {e}")
    print()
    
    # Test 8: Compare Platforms
    tests_total += 1
    print(f"Test {tests_total}: Compare Platforms")
    print("-" * 40)
    try:
        response = client.post("/api/v1/compare", json={
            "title": "Tech Review 2025",
            "platforms": ["tiktok", "instagram", "youtube"],
            "follower_counts": {
                "tiktok": 50000,
                "instagram": 75000,
                "youtube": 30000
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert "best_platform" in data
        assert "predictions" in data
        assert len(data["predictions"]) == 3
        print(f"✅ PASS - Best platform: {data['best_platform']}, "
              f"Platforms compared: {len(data['predictions'])}")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL - {e}")
    print()
    
    # Résumé
    print("=" * 80)
    print(f"📊 RÉSULTATS: {tests_passed}/{tests_total} tests passés")
    print("=" * 80)
    
    if tests_passed == tests_total:
        print("✅ ✅ ✅ TOUS LES TESTS PASSENT - BACKEND 100% FONCTIONNEL ✅ ✅ ✅")
        print()
        print("🎯 Endpoints testés:")
        print("   1. ✅ GET  /health")
        print("   2. ✅ GET  /api/v1/stats/overview (NOUVEAU)")
        print("   3. ✅ POST /api/v1/predict (avec projection_7_days)")
        print("   4. ✅ GET  /api/v1/trends/topK")
        print("   5. ✅ POST /api/v1/generate/script")
        print("   6. ✅ POST /api/v1/analyze-post (NOUVEAU)")
        print("   7. ✅ StaticFiles /outputs (FIX VIDÉO)")
        print("   8. ✅ POST /api/v1/compare")
        print()
        print("🚀 BACKEND PRÊT POUR PRODUCTION!")
        return True
    else:
        print(f"⚠️ {tests_total - tests_passed} test(s) en échec")
        return False


if __name__ == "__main__":
    success = test_backend()
    sys.exit(0 if success else 1)
