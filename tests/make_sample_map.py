"""Generate a sample map PNG to inspect the layout (dev aid)."""
import os
import sys

os.environ["DB_PATH"] = "/tmp/sample_pb.db"
if os.path.exists("/tmp/sample_pb.db"):
    os.remove("/tmp/sample_pb.db")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import db, parking_map  # noqa: E402

db.init_db()

alice = db.create_user(1001, "Alice", is_admin=True)
bob = db.create_user(1002, "Bob")
db.assign_spot(1, alice["id"])        # Alice's reserved spot (-> blue for her)
db.assign_spot(5, bob["id"])          # B2 standalone reserved
db.open_spot(db.get_spot_by_number(5)["id"], bob["id"], db.today(), None)  # free/green
db.unassign_spot(6)                   # gray (no owner)

out = "sample_map.png"
with open(out, "wb") as fh:
    fh.write(parking_map.render_map(owner_user_id=alice["id"]))

print(f"wrote {out} ({os.path.getsize(out)} bytes)")