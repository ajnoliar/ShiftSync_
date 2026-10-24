import http.server
import socketserver
import urllib.parse
import json


shifts = [
    {"id": 1, "employee": "Alice Smith", "role": "Cashier", "date": "2026-10-14", "time": "08:00 - 16:00", "hours": 8,
     "status": "Assigned"},
    {"id": 2, "employee": "Bob Jones", "role": "Stocking", "date": "2026-10-14", "time": "12:00 - 20:00", "hours": 8,
     "status": "Marketplace"},
    {"id": 3, "employee": "Charlie Cruz", "role": "Supervisor", "date": "2026-10-15", "time": "09:00 - 17:00",
     "hours": 8, "status": "Assigned"},
    {"id": 4, "employee": "Diana Ramos", "role": "Cashier", "date": "2026-10-15", "time": "14:00 - 22:00", "hours": 8,
     "status": "Assigned"}
]

swap_requests = [
    {"id": 1, "shift_id": 2, "original_employee": "Bob Jones", "date": "2026-10-14", "time": "12:00 - 20:00",
     "status": "Pending Approval", "swapped_with": "Alice Smith"}
]

availabilities = [
    {"employee": "Alice Smith", "days": "Mon, Wed, Fri", "preferred_hours": "Morning"},
    {"employee": "Bob Jones", "days": "Tue, Thu, Sat", "preferred_hours": "Evening"}
]


class ShiftSyncHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()

            # Read template file
            try:
                with open('templates/index.html', 'r', encoding='utf-8') as f:
                    html_content = f.read()

                # Dynamic Template Rendering via Simple String Replacement
                html_content = html_content.replace('{{ total_shifts }}', str(len(shifts)))
                html_content = html_content.replace('{{ marketplace_count }}',
                                                    str(len([s for s in shifts if s['status'] == 'Marketplace'])))
                html_content = html_content.replace('{{ pending_swaps }}', str(len(
                    [s for s in swap_requests if s['status'] == 'Pending Approval'])))

                # Dynamic Roster Rendering
                shift_rows = ""
                for s in shifts:
                    status_badge = '<span class="bg-amber-100 text-amber-800 text-xs px-2 py-0.5 rounded-full font-medium">In Marketplace</span>' if \
                    s[
                        'status'] == 'Marketplace' else '<span class="bg-indigo-100 text-indigo-800 text-xs px-2 py-0.5 rounded-full font-medium">Assigned Secured</span>'
                    action_button = f'<form action="/post_swap" method="POST" class="inline"><input type="hidden" name="shift_id" value="{s["id"]}"><button type="submit" class="text-xs bg-amber-50 hover:bg-amber-100 text-amber-700 font-semibold px-3 py-1.5 rounded-md border border-amber-200 transition">🚨 Drop to Marketplace</button></form>' if \
                    s[
                        'status'] == 'Assigned' else '<span class="text-xs text-gray-400 italic">Awaiting Coworker Trade</span>'

                    shift_rows += f"""
                    <tr class="hover:bg-gray-50 transition">
                        <td class="p-3 font-semibold text-gray-900">{s['employee']}</td>
                        <td class="p-3 text-gray-600">{s['role']}</td>
                        <td class="p-3 text-xs"><div class="font-medium text-gray-700">{s['date']}</div><div class="text-gray-400">{s['time']} ({s['hours']}h)</div></td>
                        <td class="p-3">{status_badge}</td>
                        <td class="p-3 text-right">{action_button}</td>
                    </tr>
                    """
                html_content = html_content.replace('<!-- SHIFT_ROWS_PLACEHOLDER -->', shift_rows)

                # Dynamic Swap Table Rendering
                swap_rows = ""
                for r in swap_requests:
                    if r['status'] == 'Pending Approval':
                        badge = '<span class="bg-blue-100 text-blue-800 text-xs px-2.5 py-1 rounded-full font-medium">Pending Review</span>'
                        actions = f"""
                        <form action="/approve_swap" method="POST" class="inline"><input type="hidden" name="req_id" value="{r['id']}"><input type="hidden" name="action" value="approve"><button type="submit" class="text-xs bg-emerald-600 hover:bg-emerald-700 text-white font-medium px-2.5 py-1 rounded shadow-sm transition">Approve</button></form>
                        <form action="/approve_swap" method="POST" class="inline"><input type="hidden" name="req_id" value="{r['id']}"><input type="hidden" name="action" value="deny"><button type="submit" class="text-xs bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium px-2.5 py-1 rounded shadow-sm transition">Deny</button></form>
                        """
                    elif r['status'] == 'Approved':
                        badge = '<span class="bg-emerald-100 text-emerald-800 text-xs px-2.5 py-1 rounded-full font-medium">✅ Approved &amp; Swapped</span>'
                        actions = '<span class="text-xs text-gray-400 italic">Transaction Finalized</span>'
                    else:
                        badge = '<span class="bg-rose-100 text-rose-800 text-xs px-2.5 py-1 rounded-full font-medium">❌ Request Denied</span>'
                        actions = '<span class="text-xs text-gray-400 italic">Transaction Finalized</span>'

                    swap_rows += f"""
                    <tr class="hover:bg-gray-50 transition">
                        <td class="p-3 font-medium text-gray-700">{r['original_employee']}</td>
                        <td class="p-3 text-xs"><div class="text-gray-800">{r['date']}</div><div class="text-gray-400">{r['time']}</div></td>
                        <td class="p-3 font-semibold text-indigo-600">{r['swapped_with']}</td>
                        <td class="p-3">{badge}</td>
                        <td class="p-3 text-right space-x-1">{actions}</td>
                    </tr>
                    """
                html_content = html_content.replace('<!-- SWAP_ROWS_PLACEHOLDER -->', swap_rows)

                # Dynamic Availability Blocks
                avail_blocks = ""
                for a in availabilities:
                    avail_blocks += f"""
                    <div class="bg-gray-50 p-3 rounded-lg border border-gray-100 text-xs flex justify-between items-center">
                        <div>
                            <div class="font-bold text-gray-800">{a['employee']}</div>
                            <div class="text-gray-500">Days: {a['days']}</div>
                        </div>
                        <span class="bg-gray-200 text-gray-700 px-2 py-1 rounded font-medium">{a['preferred_hours']}</span>
                    </div>
                    """
                html_content = html_content.replace('<!-- AVAIL_BLOCKS_PLACEHOLDER -->', avail_blocks)

                self.wfile.write(bytes(html_content, "utf-8"))
            except FileNotFoundError:
                self.wfile.write(b"Error: templates/index.html file missing.")
        else:
            super().do_GET()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        fields = urllib.parse.parse_qs(post_data)

        if self.path == '/add_shift':
            new_id = max([s['id'] for s in shifts]) + 1 if shifts else 1
            shifts.append({
                "id": new_id,
                "employee": fields.get('employee')[0],
                "role": fields.get('role')[0],
                "date": fields.get('date')[0],
                "time": fields.get('time')[0],
                "hours": int(fields.get('hours', [8])[0]),
                "status": "Assigned"
            })
        elif self.path == '/post_swap':
            s_id = int(fields.get('shift_id')[0])
            for shift in shifts:
                if shift['id'] == s_id:
                    shift['status'] = 'Marketplace'
                    new_swap_id = max([r['id'] for r in swap_requests]) + 1 if swap_requests else 1
                    swap_requests.append({
                        "id": new_swap_id,
                        "shift_id": shift['id'],
                        "original_employee": shift['employee'],
                        "date": shift['date'],
                        "time": shift['time'],
                        "status": "Pending Approval",
                        "swapped_with": "Selected Coworker"
                    })
                    break
        elif self.path == '/approve_swap':
            req_id = int(fields.get('req_id')[0])
            action = fields.get('action')[0]
            for req in swap_requests:
                if req['id'] == req_id:
                    if action == 'approve':
                        req['status'] = 'Approved'
                        for shift in shifts:
                            if shift['id'] == req['shift_id']:
                                shift['employee'] = req['swapped_with']
                                shift['status'] = 'Assigned'
                    else:
                        req['status'] = 'Denied'
                        for shift in shifts:
                            if shift['id'] == req['shift_id']:
                                shift['status'] = 'Assigned'
                    break
        elif self.path == '/submit_availability':
            availabilities.append({
                "employee": fields.get('employee')[0],
                "days": fields.get('days')[0],
                "preferred_hours": fields.get('hours')[0]
            })

        # Redirect right back to home page
        self.send_response(303)
        self.send_header('Location', '/')
        self.end_headers()


if __name__ == '__main__':
    PORT = 5001
    handler = ShiftSyncHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Server safely launched at http://localhost:{PORT}")
        httpd.serve_forever()

