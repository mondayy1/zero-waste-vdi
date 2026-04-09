import time
import os
from proxmoxer import ProxmoxAPI
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

PROXMOX_HOST = os.getenv("PROXMOX_HOST")
PROXMOX_USER = os.getenv("PROXMOX_USER")
PROXMOX_PASSWORD = os.getenv("PROXMOX_PASSWORD")
PROXMOX_NODE = os.getenv("PROXMOX_NODE", "pve")
TEMPLATE_ID = int(os.getenv("TEMPLATE_ID", "105"))

proxmox = ProxmoxAPI(
    host=PROXMOX_HOST,
    user=PROXMOX_USER,
    password=PROXMOX_PASSWORD,
    verify_ssl=False,
    timeout=60
)

def get_next_vmid():
    vms = proxmox.nodes(PROXMOX_NODE).qemu.get()
    used_ids = [vm['vmid'] for vm in vms]
    vmid = 200
    while vmid in used_ids:
        vmid += 1
    return vmid

def wait_for_clone(vmid, timeout=120):
    start = time.time()
    while time.time() - start < timeout:
        try:
            config = proxmox.nodes(PROXMOX_NODE).qemu(vmid).config.get()
            if 'lock' not in config:
                return True
        except Exception:
            pass
        time.sleep(5)
    return False

def create_vm(cpu, ram, purpose):
    if cpu > 8:
        return None, "CPU는 최대 8코어까지 가능합니다."
    if ram > 8192:
        return None, "RAM은 최대 8192MB까지 가능합니다."

    vmid = get_next_vmid()
    name = f"vdi-{purpose.lower()}-{vmid}"

    proxmox.nodes(PROXMOX_NODE).qemu(TEMPLATE_ID).clone.post(
        newid=vmid,
        name=name,
        full=1
    )

    wait_for_clone(vmid)
    time.sleep(5)

    proxmox.nodes(PROXMOX_NODE).qemu(vmid).config.put(
        cores=cpu,
        memory=ram,
        ciuser="ubuntu",
        cipassword="vdi-password",
        ide2="local-lvm:cloudinit",
        searchdomain="local",
        nameserver="8.8.8.8"
    )

    proxmox.nodes(PROXMOX_NODE).qemu(vmid).status.start.post()

    return vmid, name
