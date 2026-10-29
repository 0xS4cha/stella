import argparse
import sys
from .camera.controller import CameraController

def main():
    parser = argparse.ArgumentParser(description="Nikon D60 Controller")
    parser.add_argument("--capture", action="store_true", help="Capture an image")
    parser.add_argument("--download", action="store_true", help="Download captured image")
    parser.add_argument("--list-settings", action="store_true", help="List all camera settings")
    parser.add_argument("--get", type=str, help="Get specific setting value")
    parser.add_argument("--set", nargs=2, metavar=("NAME", "VALUE"), help="Set specific setting value")
    parser.add_argument("--load-json", type=str, metavar="FILE", help="Load settings from a JSON file")

    args = parser.parse_args()
    
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    controller = CameraController()
    
    try:
        controller.connect()
        
        if args.list_settings:
            settings = controller.get_all_settings()
            for key, value in settings.items():
                print(f"{key}: {value}")
                
        if args.get:
            value = controller.get_setting(args.get)
            print(f"{args.get}: {value}")
            
        if args.set:
            name, value = args.set
            controller.set_setting(name, value)
            print(f"Set {name} to {value}")
            
        if args.load_json:
            controller.load_settings_from_json(args.load_json)
            print(f"Loaded settings from {args.load_json}")
            
        if args.capture:
            result = controller.capture_image(download=args.download)
            print(f"Captured: {result}")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
    finally:
        controller.disconnect()

if __name__ == "__main__":
    main()