"""
Connection Tester for Phone Streams
Helps diagnose connection issues
"""

import sys
from pathlib import Path
import socket
import requests
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.live_phone_feeds.phone_stream_receiver import PhoneStreamReceiver, PhoneStreamHelper


def test_network_connectivity(phone_ip: str, port: int) -> dict:
    """Test basic network connectivity"""
    print(f"\n🔍 Testing Network Connectivity")
    print(f"   Target: {phone_ip}:{port}")
    
    results = {
        "ping": False,
        "port_open": False,
        "http_reachable": False
    }
    
    # Test ping (socket connection)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((phone_ip, port))
        sock.close()
        
        if result == 0:
            print(f"   ✅ Port {port} is open")
            results["port_open"] = True
        else:
            print(f"   ❌ Port {port} is closed or unreachable")
    except Exception as e:
        print(f"   ❌ Socket test failed: {e}")
    
    # Test HTTP
    try:
        base_url = f"http://{phone_ip}:{port}"
        response = requests.get(base_url, timeout=5)
        print(f"   ✅ HTTP server is reachable (Status: {response.status_code})")
        results["http_reachable"] = True
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Cannot connect to HTTP server")
    except requests.exceptions.Timeout:
        print(f"   ❌ HTTP request timed out")
    except Exception as e:
        print(f"   ❌ HTTP test failed: {e}")
    
    return results


def test_all_url_formats(phone_ip: str, port: int = 8080):
    """Test all common URL formats"""
    print(f"\n📱 Testing All IP Webcam URL Formats")
    print(f"   Phone IP: {phone_ip}:{port}")
    
    urls = PhoneStreamHelper.get_all_ip_webcam_urls(phone_ip, port)
    receiver = PhoneStreamReceiver()
    
    working_urls = []
    
    for url in urls:
        print(f"\n   Testing: {url}")
        result = receiver.connect_to_phone_stream(url, timeout=5)
        
        if result.get("success"):
            print(f"      ✅ SUCCESS!")
            print(f"      Resolution: {result['width']}x{result['height']}")
            working_urls.append(url)
        else:
            print(f"      ❌ Failed: {result.get('error', 'Unknown error')}")
    
    return working_urls


def main():
    """Main diagnostic tool"""
    print("=" * 60)
    print("Phone Stream Connection Diagnostic Tool")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        phone_ip = input("\nEnter your phone's IP address: ").strip()
        if not phone_ip:
            print("❌ IP address required!")
            return
    else:
        phone_ip = sys.argv[1]
    
    # Parse port if provided
    if ":" in phone_ip:
        phone_ip, port_str = phone_ip.split(":")
        port = int(port_str)
    else:
        port = 8080
        port_input = input(f"Port (default {port}): ").strip()
        if port_input:
            port = int(port_input)
    
    print(f"\n📱 Phone: {phone_ip}:{port}")
    
    # Step 1: Network connectivity
    network_results = test_network_connectivity(phone_ip, port)
    
    if not network_results["port_open"]:
        print("\n❌ Basic network connectivity failed!")
        print("\n💡 Suggestions:")
        print("   1. Ensure phone and computer are on same WiFi")
        print("   2. Check phone streaming app is running")
        print("   3. Try restarting the app")
        print("   4. Check firewall settings")
        return
    
    # Step 2: Test all URL formats
    working_urls = test_all_url_formats(phone_ip, port)
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if working_urls:
        print(f"\n✅ Found {len(working_urls)} working URL(s):")
        for url in working_urls:
            print(f"   - {url}")
        print(f"\n💡 Use this URL in your code:")
        print(f"   stream_url = \"{working_urls[0]}\"")
    else:
        print("\n❌ No working URLs found")
        print("\n💡 Try:")
        print("   1. Open URL in web browser to verify")
        print("   2. Check app settings (resolution, codec)")
        print("   3. Try different port numbers")
        print("   4. Restart phone app")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

