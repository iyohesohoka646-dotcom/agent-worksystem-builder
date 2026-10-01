"""Launch the optional SDK only when this entrypoint is selected."""
import sys

if __name__ == "__main__":
    try:
        from awb_core.mcp_server import main
        raise SystemExit(main())
    except ImportError as exc:
        print(f"MCP dependencies unavailable: {exc}. Run awb_doctor.py --project PROJECT --mcp for setup.", file=sys.stderr)
        raise SystemExit(2)
