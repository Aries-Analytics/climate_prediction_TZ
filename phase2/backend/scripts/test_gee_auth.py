
import ee
import os

def test_gee_auth():
    print("Testing GEE Authentication...")
    
    # Check env var
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "climate-prediction-using-ml")
    print(f"Project ID: {project_id}")
    
    # Check credentials file
    cred_path = "/root/.config/earthengine/credentials"
    if os.path.exists(cred_path):
        print(f"✅ Credentials file found at {cred_path}")
        with open(cred_path, 'r') as f:
            content = f.read()
            print(f"📄 Content length: {len(content)}")
    else:
        print(f"❌ Credentials file NOT found at {cred_path}")

    try:
        ee.Initialize(project=project_id)
        print("✅ ee.Initialize() SUCCESS")
    except Exception as e:
        print(f"❌ ee.Initialize() FAILED: {e}")

if __name__ == "__main__":
    test_gee_auth()
