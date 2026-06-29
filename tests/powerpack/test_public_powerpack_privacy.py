from pathlib import Path


def test_powerpack_public_skills_exist():
    root = Path(__file__).resolve().parents[2]
    required = [
        "skills/decision/SKILL.md",
        "skills/reasoning-personas/SKILL.md",
        "skills/rp/SKILL.md",
        "skills/superpowers/SKILL.md",
        "skills/productivity/present/SKILL.md",
        "skills/media/piapi-video-toolkit/SKILL.md",
        "skills/telegram/telegram-chip/SKILL.md",
        "scripts/install-powerpack.sh",
        "README-POWERPACK.md",
        "WORKSHOP-SKILLS.md",
        "skills/po/SKILL.md",
        "skills/perplex/SKILL.md",
        "skills/par/SKILL.md",
        "skills/design/refero-web-design/SKILL.md",
        "skills/hallmark/SKILL.md",
        "skills/design-pack/taste-skill/SKILL.md",
        "skills/webd/SKILL.md",
        "skills/supergoal/SKILL.md",
        "skills/devops/server-doctor/SKILL.md",
        "skills/devops/public-endpoint-ops/SKILL.md",
        "skills/infrastructure/porkbun-api-dns/SKILL.md",
        "skills/devops/supabase-project-ops/SKILL.md",
    ]
    missing = [p for p in required if not (root / p).exists()]
    assert not missing


def test_public_powerpack_files_do_not_include_private_markers():
    root = Path(__file__).resolve().parents[2]
    scanned_roots = [root / "README-POWERPACK.md", root / "skills", root / "scripts"]
    forbidden = [
        "Human" + "20",
        "human" + "20",
        "Chip" + "CR",
        "chip" + "manager",
        "617" + "744" + "661",
        "TELEGRAM_BOT_TOKEN=" + "***",
        "OPENROUTER_API_KEY=" + "***",
        "BEGIN " + "PRIVATE KEY",
    ]
    offenders = []
    for base in scanned_roots:
        paths = [base] if base.is_file() else list(base.rglob("*"))
        for path in paths:
            if not path.is_file() or ".git" in path.parts:
                continue
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4"}:
                continue
            text = path.read_text(errors="ignore")
            for marker in forbidden:
                if marker in text:
                    offenders.append((str(path.relative_to(root)), marker))
    assert offenders == []
