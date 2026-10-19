from collections import deque

class ScheduleEngine:
    DAYS = ["Luni", "Marți", "Miercuri", "Joi", "Vineri"]
    PAIRS = list(range(1, 8))
    PAIR_INTERVALS = {
        1: "08:00 - 09:30", 2: "09:45 - 11:15", 3: "11:30 - 13:00",
        4: "13:15 - 14:45", 5: "15:00 - 16:30", 6: "16:45 - 18:15", 7: "18:30 - 20:00"
    }

    @classmethod
    def generate_timeslots(cls):
        return [
            {"id": i * 7 + p, "day": d, "pair": p, "label": f"P{p} ({cls.PAIR_INTERVALS[p]})"}
            for i, d in enumerate(cls.DAYS) for p in cls.PAIRS
        ]

    @staticmethod
    def decompose_academic_hours(h):
        return ["FULL"] * (h // 2) + (["SPLIT"] if h % 2 else [])

    @classmethod
    def build_variables_and_domains(cls, groups, courses, rooms, timeslots):
        variables, var_meta, domains, capacity_errors = [], {}, {}, []
        group_map = {g["name"]: g["student_count"] for g in groups}
        max_aula_cap = max((r["capacity"] for r in rooms if r["room_type"] == "Aulă"), default=0)

        for c in sorted(courses, key=lambda x: x["priority"], reverse=True):
            requested = [g.strip() for g in c["target_groups"].split(",") if g.strip()]
            missing = [g for g in requested if g not in group_map]
            if missing:
                capacity_errors.append(
                    f"Obiectul '{c['name']}' conține grupe inexistente: {', '.join(missing)}"
                )
            assigned = list(dict.fromkeys(g for g in requested if g in group_map))
            if not assigned:
                capacity_errors.append(f"Obiectul '{c['name']}' nu are grupe valide.")
                continue

            sessions = cls.decompose_academic_hours(c["academic_hours"])
            if c["activity_type"] == "Curs":
                batches, curr_b, curr_s = [], [], 0
                for g_name in assigned:
                    cnt = group_map[g_name]
                    if curr_b and curr_s + cnt > max_aula_cap:
                        batches.append((curr_b, curr_s))
                        curr_b, curr_s = [g_name], cnt
                    else:
                        curr_b.append(g_name)
                        curr_s += cnt
                if curr_b:
                    batches.append((curr_b, curr_s))
            else:
                batches = [([g], group_map[g]) for g in assigned]

            t_room = "Aulă" if c["activity_type"] == "Curs" else c["activity_type"]

            for b_idx, (b_groups, total_stud) in enumerate(batches):
                valid_rooms = [r["name"] for r in rooms if r["room_type"] == t_room and r["capacity"] >= total_stud]
                if not valid_rooms:
                    capacity_errors.append(
                        f"• Obiectul '{c['name']}' ({c['activity_type']}) pentru [{', '.join(b_groups)}] "
                        f"necesită sală '{t_room}' cu min. {total_stud} locuri!"
                    )

                for s_idx, s_mode in enumerate(sessions):
                    vid = f"C:{c['id']}|B:{b_idx}|S:{s_idx}|M:{s_mode}"
                    variables.append(vid)
                    var_meta[vid] = {
                        "groups": b_groups, "student_count": total_stud, "course": c["name"],
                        "professor": c["professor"], "activity_type": c["activity_type"],
                        "academic_hours": c["academic_hours"], "mode": s_mode
                    }
                    domains[vid] = [
                        (s["id"], r, par)
                        for s in timeslots for r in valid_rooms
                        for par in (["FULL"] if s_mode == "FULL" else ["IMPAR", "PAR"])
                    ]
        return variables, var_meta, domains, capacity_errors

    @staticmethod
    def parities_conflict(p1, p2):
        return p1 == "FULL" or p2 == "FULL" or p1 == p2

    @classmethod
    def has_conflict(cls, val1, val2, m1, m2):
        s1, r1, p1 = val1
        s2, r2, p2 = val2
        if s1 != s2 or not cls.parities_conflict(p1, p2):
            return False
        return r1 == r2 or m1["professor"] == m2["professor"] or bool(set(m1["groups"]) & set(m2["groups"]))

    @classmethod
    def run_ac3(cls, variables, var_meta, domains):
        """Enforce arc consistency for room, professor and group conflicts."""
        if any(not domains[v] for v in variables):
            return False
        group_sets = {v: set(var_meta[v]["groups"]) for v in variables}
        room_sets = {v: {value[1] for value in domains[v]} for v in variables}
        neighbors = {v: set() for v in variables}
        for i, a in enumerate(variables):
            for b in variables[i + 1:]:
                if (group_sets[a] & group_sets[b]
                    or var_meta[a]["professor"] == var_meta[b]["professor"]
                    or room_sets[a] & room_sets[b]):
                    neighbors[a].add(b)
                    neighbors[b].add(a)
        queue = deque((a, b) for a in variables for b in neighbors[a])
        while queue:
            a, b = queue.popleft()
            ma, mb = var_meta[a], var_meta[b]
            # Keep only assignments with a compatible counterpart.
            filtered = [x for x in domains[a]
                        if any(not cls.has_conflict(x, y, ma, mb) for y in domains[b])]
            if len(filtered) != len(domains[a]):
                domains[a] = filtered
                if not filtered:
                    return False
                for other in neighbors[a] - {b}:
                    queue.append((other, a))
        return True

    @classmethod
    def beam_search(cls, variables, var_meta, domains, timeslots, beam_width=4):
        slot_lookup = {s["id"]: s for s in timeslots}
        ordered_vars = sorted(variables, key=lambda v: (0 if var_meta[v]["mode"] == "FULL" else 1, len(domains[v])))
        beam = [(0, {})]

        for vid in ordered_vars:
            meta = var_meta[vid]
            next_beam = []
            for score, state in beam:
                g_load = {g: {d: 0 for d in cls.DAYS} for g in meta["groups"]}
                same_days, half_slots = set(), set()

                for avid, (sid, _, par) in state.items():
                    ameta, sinfo = var_meta[avid], slot_lookup[sid]
                    shared = set(meta["groups"]) & set(ameta["groups"])
                    if shared:
                        for g in shared:
                            g_load[g][sinfo["day"]] += 1
                        if ameta["course"] == meta["course"]:
                            same_days.add(sinfo["day"])
                        if par in ("IMPAR", "PAR"):
                            half_slots.add((sid, par))

                candidates = []
                for cand in domains[vid]:
                    if any(cls.has_conflict(cand, a_val, meta, var_meta[avid]) for avid, a_val in state.items()):
                        continue
                    sid, r_name, par = cand
                    day, pair = slot_lookup[sid]["day"], slot_lookup[sid]["pair"]
                    avg_l = sum(g_load[g][day] for g in meta["groups"]) / len(meta["groups"])
                    bonus = 120 - pair * 7 - int(avg_l * 16) - (30 if day in same_days else 0)
                    if (par == "PAR" and (sid, "IMPAR") in half_slots) or (par == "IMPAR" and (sid, "PAR") in half_slots):
                        bonus += 50
                    candidates.append((score + bonus, cand))

                candidates.sort(key=lambda x: x[0], reverse=True)
                for n_score, cand in candidates[:beam_width * 2]:
                    next_beam.append((n_score, {**state, vid: cand}))

            if not next_beam:
                return {}
            next_beam.sort(key=lambda x: x[0], reverse=True)
            beam = next_beam[:beam_width]

        best = beam[0][1] if beam else {}
        return {
            vid: {
                **var_meta[vid], "room": r, "parity": p, "slot_id": sid,
                "day": slot_lookup[sid]["day"], "pair": slot_lookup[sid]["pair"]
            }
            for vid, (sid, r, p) in best.items()
        }

