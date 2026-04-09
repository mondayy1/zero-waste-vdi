import time
import os
from datetime import datetime
from proxmoxer import ProxmoxAPI
from dotenv import load_dotenv
import requests

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

PROXMOX_HOST = os.getenv("PROXMOX_HOST")
PROXMOX_USER = os.getenv("PROXMOX_USER")
PROXMOX_PASSWORD = os.getenv("PROXMOX_PASSWORD")
PROXMOX_NODE = os.getenv("PROXMOX_NODE", "pve")
INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG", "zero-waste")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "telegraf")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

IDLE_CPU_THRESHOLD = 10.0  # 테스트용 - CPU 10% 미만이면 유휴로 감지
IDLE_MINUTES = 10  # 테스트용 - 10분 기준
CHECK_INTERVAL = 60  # 테스트용 - 1분마다 체크
VDI_VMID_START = 200  # VDI VM은 200번대

proxmox = ProxmoxAPI(
    host=PROXMOX_HOST,
    user=PROXMOX_USER,
    password=PROXMOX_PASSWORD,
    verify_ssl=False,
    timeout=60
)


def send_discord_alert(vm_name, vmid):
    if not DISCORD_WEBHOOK:
        print("Discord 웹훅 URL이 없습니다.")
        return
    message = {
        "content": (
            f"⚠️ **[Zero-Waste 알림]**\n"
            f"VM `{vm_name}` (ID: {vmid})이 24시간 이상 유휴 상태입니다.\n"
            f"24시간 내 응답이 없으면 자동 회수됩니다."
        )
    }
    try:
        response = requests.post(DISCORD_WEBHOOK, json=message)
        print(f"Discord 응답: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Discord 알림 실패: {e}")


def get_idle_vms():
    """InfluxDB에서 24시간 평균 CPU가 1% 미만인 VM 목록 반환"""
    from influxdb_client import InfluxDBClient

    client = InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    )

    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -{IDLE_MINUTES}h)
      |> filter(fn: (r) => r._measurement == "cpu")
      |> filter(fn: (r) => r._field == "usage_idle")
      |> filter(fn: (r) => r.cpu == "cpu-total")
      |> mean()
      |> filter(fn: (r) => r._value > {100 - IDLE_CPU_THRESHOLD})
    '''

    try:
        result = client.query_api().query(query)
        idle_hosts = []
        for table in result:
            for record in table.records:
                idle_hosts.append(record.values.get("host"))
        return idle_hosts
    except Exception as e:
        print(f"InfluxDB 조회 실패: {e}")
        return []
    finally:
        client.close()


def snapshot_and_stop(vmid, vm_name):
    """스냅샷 생성 후 VM 정지"""
    snap_name = f"auto-{datetime.now().strftime('%Y%m%d%H%M')}"
    try:
        print(f"[{vm_name}] 스냅샷 생성 중: {snap_name}")
        proxmox.nodes(PROXMOX_NODE).qemu(vmid).snapshot.post(snapname=snap_name)
        time.sleep(10)
        print(f"[{vm_name}] VM 정지 중")
        proxmox.nodes(PROXMOX_NODE).qemu(vmid).status.stop.post()
        print(f"[{vm_name}] 자동 회수 완료")
    except Exception as e:
        print(f"[{vm_name}] 회수 실패: {e}")


def get_vdi_vms():
    """200번대 VDI VM 목록 반환"""
    try:
        vms = proxmox.nodes(PROXMOX_NODE).qemu.get()
        return [vm for vm in vms if vm['vmid'] >= VDI_VMID_START and vm['status'] == 'running']
    except Exception as e:
        print(f"VM 목록 조회 실패: {e}")
        return []


def main():
    print("Zero-Waste 데몬 시작")
    while True:
        print(f"\n유휴 VM 체크 중...")

        idle_hosts = get_idle_vms()
        vdi_vms = get_vdi_vms()

        for vm in vdi_vms:
            vmid = vm['vmid']
            vm_name = vm.get('name', str(vmid))

            if vm_name in idle_hosts:
                print(f"[{vm_name}] 유휴 상태 감지")
                send_discord_alert(vm_name, vmid)
                snapshot_and_stop(vmid, vm_name)
            else:
                print(f"[{vm_name}] 정상 사용 중")

        print(f"다음 체크까지 {CHECK_INTERVAL}초 대기")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
