def summarize_absences(fixture_json):
    """Convert Sportmonks sidelined records into model features.

    The model should use only records whose start/end dates establish
    unavailability at prediction time. Do not use post-kickoff information.
    """
    data=fixture_json.get("data",fixture_json)
    sidelined=data.get("sidelined",[]) or []
    home_count=away_count=0
    rows=[]
    for x in sidelined:
        player=x.get("player") or {}
        team_id=x.get("team_id") or x.get("participant_id")
        rows.append({
            "player_id":player.get("id"),
            "player":player.get("display_name") or player.get("name"),
            "team_id":team_id,
            "reason":(x.get("type") or {}).get("name"),
            "start":x.get("start_date"),
            "end":x.get("end_date"),
        })
    return rows
