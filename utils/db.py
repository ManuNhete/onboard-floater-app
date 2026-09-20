from utils.supabase_client import get_client

DOCS_BUCKET = "driver-documents"


def get_driver_by_phone(phone_number: str):
    """Returns the driver row for a phone number, or None if not found."""
    client = get_client()
    res = (
        client.table("drivers")
        .select("*")
        .eq("phone_number", phone_number)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def create_driver_profile(form_data: dict) -> dict:
    """Inserts a new driver row and returns it (including its generated id)."""
    client = get_client()
    payload = {
               "phone_number": form_data["phone_number"],
        "full_name": form_data.get("full_name"),
        "dob": form_data.get("dob"),
        "national_id": form_data.get("national_id"),
        "address": form_data.get("address"),
        "vehicle_type": form_data.get("vehicle_type"),
        "plate_number": form_data.get("plate_number"),
        "payout_method": form_data.get("payout_method"),
        "status": "pending",
    }
    res = client.table("drivers").insert(payload).execute()
    return res.data[0]


def upload_document(driver_id: str, doc_type: str, file_bytes: bytes, file_name: str) -> str:
    """Uploads a document to Supabase Storage and records it in driver_documents."""
    client = get_client()
    ext = file_name.split(".")[-1] if "." in file_name else "bin"
    path = f"{driver_id}/{doc_type}.{ext}"

    client.storage.from_(DOCS_BUCKET).upload(
        path,
        file_bytes,
        {"upsert": "true"},
    )
    client.table("driver_documents").insert(
        {
            "driver_id": driver_id,
            "doc_type": doc_type,
            "file_path": path,
        }
    ).execute()
    return path