# -*- coding: utf-8 -*-
"""English + Armenian user-facing strings.

Use :func:`t` with a ``lang`` code (``"en"``/``"hy"``). English is the
fallback for missing keys. Templates use ``str.format`` placeholders.
"""
from __future__ import annotations

LANGS = ("en", "hy")
LANG_NAMES = {"en": "English", "hy": "Հայերեն"}

MONTHS = {
    "en": [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ],
    "hy": [
        "Հունվար", "Փետրվար", "Մարտ", "Ապրիլ", "Մայիս", "Հունիս",
        "Հուլիս", "Օգոստոս", "Սեպտեմբեր", "Հոկտեմբեր", "Նոյեմբեր", "Դեկտեմբեր",
    ],
}
MONTHS_ABBR = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "hy": ["Հնվ", "Փտվ", "Մրտ", "Ապր", "Մյս", "Հնս",
           "Հլս", "Օգս", "Սպտ", "Հոկ", "Նոյ", "Դեկ"],
}
WEEKDAYS = {
    "en": ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
    "hy": ["Եկ", "Եք", "Չո", "Հի", "Ուր", "Շբ", "Կի"],
}

STRINGS = {
    # --- buttons ---
    "btn_status": {"en": "📋 My status", "hy": "📋 Իմ կարգավիճակը"},
    "btn_map": {"en": "🗺️ Where I park", "hy": "🗺️ Որտեղ եմ կայանում"},
    "btn_open": {"en": "🔓 Open my spot", "hy": "🔓 Կիսվել իմ տեղով"},
    "btn_close": {"en": "🔒 Close my spot", "hy": "🔒 Փակել իմ տեղը"},
    "btn_avail": {"en": "🅿️ Available spots", "hy": "🅿️ Ազատ տեղեր"},
    "btn_claim": {"en": "🚗 I parked", "hy": "🚗 Կայանել եմ"},
    "btn_release": {"en": "✅ I left (release)", "hy": "✅ Հեռացա"},
    "btn_cancel": {"en": "✖️ Cancel", "hy": "✖️ Չեղարկել"},
    "btn_menu": {"en": "🏠 Main menu", "hy": "🏠 Գլխավոր մենյու"},
    "btn_lang": {"en": "🌐 Language", "hy": "🌐 Լեզու"},
    "btn_open_days": {"en": "✅ Open these days", "hy": "✅ Բացել այս օրերը"},
    "btn_until": {"en": "♾️ Until I close it", "hy": "♾️ Մինչև փակեմ"},
    "btn_today": {"en": "📍 Today", "hy": "📍 Այսօր"},
    "btn_pick": {"en": "📅 Pick a date", "hy": "📅 Ընտրել ամսաթիվ"},
    "btn_back_days": {"en": "◀ Back to days", "hy": "◀ Վերադառնալ օրերին"},
    "btn_close_days": {"en": "🔒 Close selected days", "hy": "🔒 Փակել ընտրված օրերը"},
    "btn_close_all": {"en": "🔒 Close ALL days", "hy": "🔒 Փակել ԲՈԼՈՐ օրերը"},
    "btn_approve": {"en": "✅ Approve", "hy": "✅ Հաստատել"},
    "btn_reject": {"en": "⛔ Reject", "hy": "⛔ Մերժել"},
    # --- command descriptions ---
    "cmd_start": {"en": "Register / main menu", "hy": "Գրանցում / գլխավոր մենյու"},
    "cmd_menu": {"en": "Main menu", "hy": "Գլխավոր մենյու"},
    "cmd_status": {"en": "My spot and today", "hy": "Իմ տեղն ու այսօրը"},
    "cmd_map": {"en": "Parking map", "hy": "Կայանատեղիի քարտեզ"},
    "cmd_open": {"en": "Share my spot", "hy": "Կիսվել իմ տեղով"},
    "cmd_close": {"en": "Stop sharing my spot", "hy": "Դադարեցնել կիսվելը"},
    "cmd_available": {"en": "Free spots today", "hy": "Այսօր ազատ տեղեր"},
    "cmd_claim": {"en": "I parked in a free spot", "hy": "Կայանել եմ ազատ տեղում"},
    "cmd_release": {"en": "I left my claimed spot", "hy": "Հեռացա զբաղեցրած տեղից"},
    "cmd_help": {"en": "Help", "hy": "Օգնություն"},
    "cmd_language": {"en": "Switch language", "hy": "Փոխել լեզուն"},
    "cmd_admin": {"en": "Admin help", "hy": "Ադմինի օգնություն"},
    "cmd_adduser": {"en": "Pre-create a user account", "hy": "Ստեղծել օգտատեր"},
    "cmd_deluser": {"en": "Delete a user", "hy": "Ջնջել օգտատիրոջը"},
    "cmd_makeadmin": {"en": "Grant admin rights", "hy": "Դարձնել ադմին"},
    "cmd_demote": {"en": "Remove admin rights", "hy": "Հեռացնել ադմինի իրավունքը"},
    "cmd_users": {"en": "Users and pending requests", "hy": "Օգտատերեր և հայտեր"},
    "cmd_approve": {"en": "Approve a registration (by telegram id)",
                    "hy": "Հաստատել գրանցումը (telegram id-ով)"},
    "cmd_reject": {"en": "Reject a registration (by telegram id)",
                   "hy": "Մերժել գրանցումը (telegram id-ով)"},
    "cmd_spots": {"en": "List all spots", "hy": "Ցույց տալ բոլոր տեղերը"},
    "cmd_assign": {"en": "Assign a spot to a user", "hy": "Տեղ հատկացնել օգտատիրոջը"},
    "cmd_unassign": {"en": "Remove a spot owner", "hy": "Հեռացնել տեղի տիրոջը"},
    "cmd_settype": {"en": "Set spot type", "hy": "Փոխել տեղի տեսակը"},
    "cmd_rename": {"en": "Fix a user's display name", "hy": "Փոխել օգտատիրոջ անունը"},
    "cmd_resetclaims": {"en": "Clear today's claims", "hy": "Մաքրել այսօրվա զբաղեցումները"},
    "cmd_cycle": {"en": "Show rotation cycles", "hy": "Ցույց տալ հերթափոխները"},
    "cmd_addcycles": {"en": "Add rotation cycles (paste a plan)",
                      "hy": "Ավելացնել հերթափոխ (տեղադրել պլան)"},
    "cmd_delcycle": {"en": "Delete a rotation cycle by id",
                     "hy": "Ջնջել հերթափոխը id-ով"},
    "cmd_clearcycles": {"en": "Remove all rotation cycles",
                        "hy": "Ջնջել բոլոր հերթափոխները"},
    # --- generic ---
    "admin_only": {"en": "⛔ This command is for the admin only.",
                   "hy": "⛔ Այս հրամանը միայն ադմինի համար է։"},
    "not_registered": {"en": "You're not registered yet. Send /start and tell me your name first.",
                       "hy": "Դուք դեռ գրանցված չեք։ Նախ ուղարկեք /start և գրեք ձեր անունը։"},
    "what_next": {"en": "What would you like to do?",
                  "hy": "Ի՞նչ կցանկանայիք անել։"},
    "buttons_only": {"en": "I only understand buttons and commands. Use /menu to get started.",
                     "hy": "Ես հասկանում եմ միայն կոճակներ և հրամաններ։ Սկսելու համար օգտվեք /menu-ից։"},
    "lang_now": {"en": "🌐 Language: <b>English</b>.",
                 "hy": "🌐 Լեզուն՝ <b>Հայերեն</b>։"},
    "lang_pick": {"en": "🌐 <b>Choose your language</b>",
                  "hy": "🌐 <b>Ընտրեք լեզուն</b>"},
    "type_reserved": {"en": "reserved", "hy": "ամրագրված"},
    "type_rotating": {"en": "rotating", "hy": "հերթափոխային"},
    "no_owner": {"en": "<i>unassigned</i>", "hy": "<i>առանց տիրոջ</i>"},
    # --- registration ---
    "welcome": {
        "en": ("👋 <b>Welcome to the office parking bot!</b>\n\n"
               "I keep track of who has which parking spot and let colleagues share a "
               "spot when they don't drive to the office.\n\n"
               "An admin has to approve you before you can start. Send the <b>name</b> "
               "the admin told you to use (it must match), or your own name if you're "
               "new — the admin will get a message to confirm you."),
        "hy": ("👋 <b>Բարի գալուստ գրասենյակի կայանատեղիի բոտ։</b>\n\n"
               "Ես հետևում եմ, թե ով որ կայանատեղին ունի, և թույլ եմ տալիս գործընկերներին "
               "կիսվել տեղով, երբ մեքենայով չեն գալիս գրասենյակ։\n\n"
               "Սկսելուց առաջ ադմինը պետք է հաստատի ձեզ։ Ուղարկեք <b>անունը</b>, որը ադմինը "
               "ձեզ ասել է օգտագործել (պետք է համընկնի), կամ ձեր անունը, եթե նոր եք — "
               "ադմինը կստանա հաստատման հաղորդագրություն։"),
    },
    "waiting": {
        "en": ("⏳ Your registration request is waiting for the admin to approve it. "
               "You'll be notified here as soon as it's confirmed."),
        "hy": ("⏳ Ձեր գրանցման հայտը սպասում է ադմինի հաստատմանը։ "
               "Հաստատվելուն պես այստեղ կտեղեկացվեք։"),
    },
    "welcome_back": {"en": "Welcome back, {name}! What would you like to do?",
                     "hy": "Բարի վերադարձ, {name}։ Ի՞նչ կցանկանայիք անել։"},
    "name_length": {"en": "Please send a name between 1 and 40 characters.",
                    "hy": "Խնդրում ենք ուղարկել 1–40 նիշանոց անուն։"},
    "name_taken": {"en": "Someone is already named <b>{name}</b>. Please send a different name.",
                   "hy": "<b>{name}</b> անունով մեկն արդեն կա։ Խնդրում ենք ուղարկել այլ անուն։"},
    "registered_admin": {
        "en": ("Nice to meet you, {name}! You're registered.\n\n"
               "👑 You've been set up as the <b>admin</b>. Use /help to see the "
               "admin commands for assigning spots."),
        "hy": ("Ուրախ եմ ծանոթանալ, {name}։ Դուք գրանցված եք։\n\n"
               "👑 Դուք նշանակվել եք <b>ադմին</b>։ Տեղեր հատկացնելու հրամանները "
               "տեսնելու համար օգտվեք /help-ից։"),
    },
    "approved_dm": {"en": "🎉 <b>You're approved!</b> Welcome to the parking bot.\n\nUse /menu to get started.",
                    "hy": "🎉 <b>Դուք հաստատված եք։</b> Բարի գալուստ կայանատեղիի բոտ։\n\nՍկսելու համար օգտվեք /menu-ից։"},
    "rejected_dm": {"en": "Your registration request was <b>rejected</b> by the admin.",
                    "hy": "Ձեր գրանցման հայտը <b>մերժվել է</b> ադմինի կողմից։"},
    "new_request": {
        "en": ("🔔 <b>New registration request</b>\n\n"
               "Name: <b>{name}</b>\n"
               "Telegram id: <code>{tg}</code>{username}\n\n"
               "Tap a button below, or use /users, /approve, /reject."),
        "hy": ("🔔 <b>Գրանցման նոր հայտ</b>\n\n"
               "Անուն՝ <b>{name}</b>\n"
               "Telegram id՝ <code>{tg}</code>{username}\n\n"
               "Սեղմեք ներքևի կոճակը կամ օգտվեք /users, /approve, /reject հրամաններից։"),
    },
    "help": {
        "en": ("<b>Parking bot — help</b>\n\n"
               "<b>Everyone</b>\n"
               "• /map — parking map: green free, red in use, blue yours\n"
               "• /status — your spot and today's situation\n"
               "• /available — spots that are free today\n"
               "• /open — pick the day(s) your spot is free\n"
               "• /close — take back specific days (or stop sharing)\n"
               "• /claim — record that you parked in a free spot\n"
               "• /release — record that you left that spot\n"
               "• /menu — main menu, /language — switch language, /help — this text\n\n"
               "<b>Admin only</b>\n"
               "• /adduser &lt;name&gt; — pre-create a user account\n"
               "• /deluser &lt;name or tg-id&gt; — delete a user\n"
               "• /makeadmin &lt;name or tg-id&gt; — grant admin rights\n"
               "• /demote &lt;name or tg-id&gt; — remove admin rights\n"
               "• /spots — list every spot and its state\n"
               "• /users — list users and pending requests\n"
               "• /assign &lt;spot&gt; &lt;name&gt; — give a spot to a user\n"
               "• /unassign &lt;spot or name&gt; — remove the owner of a spot\n"
               "• /settype &lt;spot&gt; reserved|rotating — change a spot type\n"
               "• /rename &lt;name&gt; &lt;new name&gt; — fix a user's display name\n"
               "• /resetclaims — clear today's \"I parked\" marks\n"
               "• /cycle — show the rotation cycles (who has what, until when)\n"
               "• /addcycles — add rotation cycles by pasting a plan\n"
               "• /delcycle, /clearcycles — remove cycles\n"),
        "hy": ("<b>Կայանատեղիի բոտ — օգնություն</b>\n\n"
               "<b>Բոլորի համար</b>\n"
               "• /map — քարտեզ. կանաչը՝ ազատ, կարմիրը՝ զբաղված, կապույտը՝ ձերը\n"
               "• /status — ձեր տեղն ու այսօրվա իրավիճակը\n"
               "• /available — այսօր ազատ տեղեր\n"
               "• /open — նշել օր(եր)ը, երբ ձեր տեղն ազատ է\n"
               "• /close — հետ վերցնել օրեր (կամ դադարեցնել կիսվելը)\n"
               "• /claim — նշել, որ կայանել եք ազատ տեղում\n"
               "• /release — նշել, որ հեռացել եք տեղից\n"
               "• /menu — գլխավոր մենյու, /language — փոխել լեզուն, /help — այս տեքստը\n\n"
               "<b>Միայն ադմինի համար</b>\n"
               "• /adduser &lt;անուն&gt; — նախապես ստեղծել օգտատեր\n"
               "• /deluser &lt;անուն կամ tg-id&gt; — ջնջել օգտատիրոջը\n"
               "• /makeadmin &lt;անուն կամ tg-id&gt; — դարձնել ադմին\n"
               "• /demote &lt;անուն կամ tg-id&gt; — հեռացնել ադմինի իրավունքը\n"
               "• /spots — ցույց տալ բոլոր տեղերն ու դրանց վիճակը\n"
               "• /users — ցույց տալ օգտատերերին և սպասող հայտերը\n"
               "• /assign &lt;տեղ&gt; &lt;անուն&gt; — տեղ հատկացնել օգտատիրոջը\n"
               "• /unassign &lt;տեղ կամ անուն&gt; — հեռացնել տեղի տիրոջը\n"
               "• /settype &lt;տեղ&gt; reserved|rotating — փոխել տեղի տեսակը\n"
               "• /rename &lt;անուն&gt; &lt;նոր անուն&gt; — փոխել օգտատիրոջ անունը\n"
               "• /resetclaims — մաքրել այսօրվա «կայանել եմ» նշումները\n"
               "• /cycle — ցույց տալ հերթափոխները (ով՝ ինչ, մինչև երբ)\n"
               "• /addcycles — ավելացնել հերթափոխ՝ տեղադրելով պլան\n"
               "• /delcycle, /clearcycles — ջնջել հերթափոխները\n"),
    },
    # --- status / available ---
    "status_title": {"en": "📋 <b>Status for {name}</b>",
                     "hy": "📋 <b>Կարգավիճակ — {name}</b>"},
    "your_spot": {"en": "Your spot: <b>#{n}</b> ({type})",
                  "hy": "Ձեր տեղը՝ <b>#{n}</b> ({type})"},
    "spot_open": {"en": "🔓 Marked <b>open</b> — colleagues can take it today.",
                  "hy": "🔓 Նշված է <b>բաց</b> — գործընկերները կարող են այսօր օգտվել։"},
    "spot_taken": {"en": "🚗 Taken today by <b>{who}</b>.",
                   "hy": "🚗 Այսօր զբաղված է՝ <b>{who}</b>։"},
    "spot_locked": {"en": "🔒 Reserved for you (not shared).",
                    "hy": "🔒 Ձերն է (չի կիսվում)։"},
    "rotation_until": {"en": "⏳ Rotation valid until <b>{end}</b>.",
                       "hy": "⏳ Հերթափոխը գործում է մինչև <b>{end}</b>։"},
    "no_spot": {"en": "You don't have a reserved or rotating spot.",
                "hy": "Դուք ամրագրված տեղ չունեք։"},
    "parked_here": {"en": "🚗 You are parked in spot <b>#{n}</b> today.",
                    "hy": "🚗 Այսօր կայանել եք <b>#{n}</b> տեղում։"},
    "check_avail": {"en": "Check <b>Available spots</b> to find one you can use.",
                    "hy": "Օգտվեք <b>Ազատ տեղեր</b> կոճակից՝ հարմար տեղ գտնելու համար։"},
    "free_today": {"en": "🅿️ <b>Free spots today</b> ({day})",
                   "hy": "🅿️ <b>Այսօր ազատ տեղեր</b> ({day})"},
    "freed_by": {"en": "<b>#{n}</b> — freed by {who}",
                 "hy": "<b>#{n}</b> — ազատել է {who}"},
    "unassigned_free": {"en": "<b>#{n}</b> — unassigned (always free)",
                        "hy": "<b>#{n}</b> — առանց տիրոջ (միշտ ազատ)"},
    "no_free": {"en": "No spots are open right now.",
                "hy": "Այս պահին բաց տեղեր չկան։"},
    "owns_block": {"en": ("You already have your own spot — available spots are for "
                          "colleagues without one."),
                   "hy": ("Դուք արդեն ունեք ձեր տեղը — ազատ տեղերը նրանց համար են, "
                          "ովքեր տեղ չունեն։")},
    "claim_block": {"en": "You already have your own spot, so you can't take someone else's.",
                    "hy": "Դուք ունեք ձեր տեղը, ուրիշի տեղը չեք կարող զբաղեցնել։"},
    "release_block": {"en": ("You have your own spot, so claiming/releasing shared spots "
                             "doesn't apply to you."),
                      "hy": ("Դուք ունեք ձեր տեղը, այնպես որ ուրիշի տեղը զբաղեցնելը/"
                             "ազատելը ձեզ չի վերաբերում։")},
    # --- map ---
    "map_caption": {
        "en": ("🅿️ <b>Office Parking</b>\n"
               "Blue = your spot · Green = free · Red = in use · Gray = no owner"),
        "hy": ("🅿️ <b>Գրասենյակի կայանատեղի</b>\n"
               "Կապույտը՝ ձեր տեղն է · Կանաչը՝ ազատ · Կարմիրը՝ զբաղված · Մոխրագույնը՝ առանց տիրոջ"),
    },
    "map_day": {"en": "📅 <b>{day}</b>\n🟢 Free on this day: {free}",
                "hy": "📅 <b>{day}</b>\n🟢 Այս օրը ազատ են՝ {free}"},
    "map_none": {"en": "none", "hy": "չկան"},
    "map_pick": {"en": "📅 <b>Pick a date</b> to see which spots are free that day.",
                 "hy": "📅 <b>Ընտրեք ամսաթիվ</b>՝ տեսնելու, թե որ տեղերն են ազատ այդ օրը։"},
    "map_render_fail": {
        "en": "Something went wrong rendering the map. Make sure Pillow is installed and layout.py is valid.",
        "hy": "Քարտեզը գծելիս սխալ տեղի ունեցավ։ Ստուգեք, որ Pillow-ն տեղադրված է, իսկ layout.py-ը՝ ճիշտ։"},
    "map_send_fail": {"en": "Could not send the map image.",
                      "hy": "Չհաջողվեց ուղարկել քարտեզի նկարը։"},
    # --- open picker ---
    "open_title": {
        "en": ("<b>Share spot #{n}</b>\n"
               "Tap the day(s) you won't drive, then <b>Open these days</b>.\n"
               "Selected: {pretty}{note}"),
        "hy": ("<b>Կիսվել #{n} տեղով</b>\n"
               "Նշեք օր(եր)ը, երբ մեքենայով չեք գալիս, ապա՝ <b>Բացել այս օրերը</b>։\n"
               "Ընտրված է՝ {pretty}{note}"),
    },
    "open_note": {"en": "\n<i>Rotation plan valid until {end}.</i>",
                  "hy": "\n<i>Հերթափոխի պլանը գործում է մինչև {end}։</i>"},
    "sel_none": {"en": "none yet", "hy": "դեռ ոչինչ"},
    "sel_none_close": {"en": "none", "hy": "ոչինչ"},
    "no_share": {"en": "You don't own a spot, so there's nothing to share.",
                 "hy": "Դուք տեղ չունեք, կիսվելու բան չկա։"},
    "no_spot_short": {"en": "You don't own a spot.", "hy": "Դուք տեղ չունեք։"},
    "opened_until": {
        "en": ("🔓 Spot <b>#{n}</b> is now open until you close it. "
               "Colleagues without a spot can take it."),
        "hy": ("🔓 <b>#{n}</b> տեղն այժմ բաց է՝ մինչև փակեք այն։ "
               "Տեղ չունեցող գործընկերները կարող են օգտվել։")},
    "opened_days": {
        "en": ("🔓 Spot <b>#{n}</b> is now open on: {pretty}.\n"
               "Colleagues without a spot can take it."),
        "hy": ("🔓 <b>#{n}</b> տեղն այժմ բաց է հետևյալ օրերին՝ {pretty}։\n"
               "Տեղ չունեցող գործընկերները կարող են օգտվել։")},
    # --- close picker ---
    "close_title": {
        "en": ("<b>Stop sharing spot #{n}</b>\n"
               "Tap the day(s) you want to take back, then <b>Close selected days</b> "
               "(or <b>Close ALL days</b>).\n"
               "Selected: {pretty}"),
        "hy": ("<b>Դադարեցնել #{n} տեղի կիսվելը</b>\n"
               "Նշեք օր(եր)ը, որոնք ցանկանում եք հետ վերցնել, ապա՝ <b>Փակել ընտրված օրերը</b> "
               "(կամ <b>Փակել ԲՈԼՈՐ օրերը</b>)։\n"
               "Ընտրված է՝ {pretty}"),
    },
    "close_more": {"en": "\n<i>Showing the next {max} days.</i>",
                   "hy": "\n<i>Ցուցադրվում են հաջորդ {max} օրերը։</i>"},
    "not_shared": {"en": "Your spot <b>#{n}</b> isn't shared right now.",
                   "hy": "Ձեր <b>#{n}</b> տեղը հիմա չի կիսվում։"},
    "closed_all": {"en": "🔒 Spot <b>#{n}</b> is no longer shared.",
                   "hy": "🔒 <b>#{n}</b> տեղն այլևս չի կիսվում։"},
    "closed_days": {
        "en": ("🔒 Closed <b>{count}</b> day(s): {pretty}.\n"
               "The spot stays shared on the remaining days."),
        "hy": ("🔒 Փակվեց <b>{count}</b> օր՝ {pretty}։\n"
               "Մնացած օրերին տեղը շարունակում է կիսվել։")},
    # --- claim / release ---
    "already_parked": {"en": "You already parked in <b>#{n}</b> today. Release it first if you moved.",
                       "hy": "Այսօր արդեն կայանել եք <b>#{n}</b>-ում։ Եթե տեղափոխվել եք, նախ ազատեք այն։"},
    "already_active": {"en": "You already have an active spot for today.",
                       "hy": "Այսօրվա համար արդեն ակտիվ տեղ ունեք։"},
    "no_free_claim": {"en": "There are no free spots to claim today.",
                      "hy": "Այսօր զբաղեցնելու ազատ տեղեր չկան։"},
    "claim_which": {"en": "Which spot did you park in? Tap the number:",
                    "hy": "Ո՞ր տեղում եք կայանել։ Սեղմեք համարը։"},
    "no_release": {"en": "You have no active spot to release today.",
                   "hy": "Այսօր ազատելու ակտիվ տեղ չունեք։"},
    "released": {"en": "✅ Released spot <b>#{n}</b>. It's free for others again.",
                 "hy": "✅ <b>#{n}</b> տեղն ազատվեց։ Այն նորից ազատ է մյուսների համար։"},
    "claimed": {
        "en": ("🚗 You're parked in <b>#{n}</b> today.\n"
               "Your claim is only for today — it releases automatically at midnight. "
               "Tap <b>I left (release)</b> when you leave so others can use it right away."),
        "hy": ("🚗 Այսօր կայանել եք <b>#{n}</b>-ում։\n"
               "Զբաղեցումը միայն այսօրվա համար է — կեսգիշերին ավտոմատ կազատվի։ "
               "Հեռանալիս սեղմեք <b>Հեռացա</b>, որ մյուսներն անմիջապես օգտվեն։")},
    "own_spot": {"en": "That's your own spot.", "hy": "Դա ձեր սեփական տեղն է։"},
    "no_spot_num": {"en": "That spot doesn't exist.", "hy": "Այդպիսի տեղ չկա։"},
    "unknown_spot": {"en": "Unknown spot.", "hy": "Անհայտ տեղ։"},
    "spot_gone": {"en": "Spot <b>#{n}</b> is no longer available.",
                  "hy": "<b>#{n}</b> տեղն այլևս հասանելի չէ։"},
    "claim_unassigned": {"en": "#{n} (unassigned)", "hy": "#{n} (առանց տիրոջ)"},
    "claim_was": {"en": "#{n} (was {who})", "hy": "#{n} ({who}-ից)"},
    # --- midnight sweep ---
    "sweep_open": {
        "en": ("🌅 New day — your claim on spot <b>#{n}</b> is released automatically. "
               "The owner is still sharing it today, so others can claim it."),
        "hy": ("🌅 Նոր օր — <b>#{n}</b> տեղի ձեր զբաղեցումն ավտոմատ ազատվեց։ "
               "Տերը այսօր էլ է կիսվում, այնպես որ մյուսները կարող են զբաղեցնել։")},
    "sweep_closed": {
        "en": ("🌅 New day — your claim on spot <b>#{n}</b> has ended because the owner "
               "is using the spot again."),
        "hy": ("🌅 Նոր օր — <b>#{n}</b> տեղի ձեր զբաղեցումն ավարտվեց, քանի որ տերն "
               "նորից է օգտվում տեղից։")},
    # --- admin ---
    "admin_help": {
        "en": ("<b>Admin commands</b>\n\n"
               "• /adduser &lt;name&gt; — pre-create a user account\n"
               "• /deluser &lt;name or tg-id&gt; — delete a user\n"
               "• /makeadmin &lt;name or tg-id&gt; — grant admin rights\n"
               "• /demote &lt;name or tg-id&gt; — remove admin rights\n"
               "• /users — registered users and pending requests\n"
               "• /spots — every spot, owner and today's state\n"
               "• /assign &lt;spot#&gt; &lt;name or telegram-id&gt; — give a spot\n"
               "• /unassign &lt;spot# or name&gt; — free a spot (or a user's spot)\n"
               "• /settype &lt;spot#&gt; reserved|rotating — change type\n"
               "• /rename &lt;name or telegram-id&gt; &lt;new name&gt; — fix a display name\n"
               "• /resetclaims — clear all of today's \"I parked\" marks\n"
               "• /cycle — show rotation cycles (who has what, until when)\n"
               "• /addcycles — add one or more cycles by pasting a plan\n"
               "• /delcycle &lt;id&gt; · /clearcycles — remove cycles\n\n"
               "New people who message the bot are sent to you for approval before "
               "they can use it.\n\n"
               "For the 3-month rotation, use /addcycles with a block like:\n"
               "<pre>Cycle 1 12/10/26-31/12/26\n1 - Alice\n2 - Bob</pre>"),
        "hy": ("<b>Ադմինի հրամաններ</b>\n\n"
               "• /adduser &lt;անուն&gt; — նախապես ստեղծել օգտատեր\n"
               "• /deluser &lt;անուն կամ tg-id&gt; — ջնջել օգտատիրոջը\n"
               "• /makeadmin &lt;անուն կամ tg-id&gt; — դարձնել ադմին\n"
               "• /demote &lt;անուն կամ tg-id&gt; — հեռացնել ադմինի իրավունքը\n"
               "• /users — գրանցված օգտատերեր և սպասող հայտեր\n"
               "• /spots — բոլոր տեղերը, տերերն ու այսօրվա վիճակը\n"
               "• /assign &lt;տեղ#&gt; &lt;անուն կամ telegram-id&gt; — տեղ հատկացնել\n"
               "• /unassign &lt;տեղ# կամ անուն&gt; — ազատել տեղը (կամ օգտատիրոջ տեղը)\n"
               "• /settype &lt;տեղ#&gt; reserved|rotating — փոխել տեսակը\n"
               "• /rename &lt;անուն կամ telegram-id&gt; &lt;նոր անուն&gt; — փոխել անունը\n"
               "• /resetclaims — մաքրել այսօրվա բոլոր «կայանել եմ» նշումները\n"
               "• /cycle — ցույց տալ հերթափոխները (ով՝ ինչ, մինչև երբ)\n"
               "• /addcycles — ավելացնել հերթափոխ՝ տեղադրելով պլան\n"
               "• /delcycle &lt;id&gt; · /clearcycles — ջնջել հերթափոխները\n\n"
               "Նոր մարդիկ, ովքեր գրում են բոտին, ուղարկվում են ձեզ հաստատման՝ "
               "նախքան օգտվելը։\n\n"
               "3-ամսյա հերթափոխի համար /addcycles-ով ուղարկեք այսպիսի բլոկ.\n"
               "<pre>Cycle 1 12/10/26-31/12/26\n1 - Անուն\n2 - Անուն2</pre>"),
    },
    "usage_adduser": {"en": "Usage: /adduser &lt;name&gt;",
                      "hy": "Օգտագործում՝ /adduser &lt;անուն&gt;"},
    "name_len": {"en": "The name must be between 1 and 40 characters.",
                 "hy": "Անունը պետք է լինի 1–40 նիշանոց։"},
    "user_exists": {"en": "A user named <b>{name}</b> already exists. Use /rename to change it.",
                    "hy": "<b>{name}</b> անունով օգտատեր արդեն կա։ Փոխելու համար օգտվեք /rename-ից։"},
    "user_created": {
        "en": ("✅ Created <b>{name}</b>. When they send /start and type "
               "that exact name, you'll get a prompt to confirm them."),
        "hy": ("✅ <b>{name}</b> ստեղծվեց։ Երբ նա ուղարկի /start և գրի հենց այդ անունը, "
               "դուք կստանաք հաստատման հարցում։")},
    "usage_deluser": {"en": "Usage: /deluser &lt;name or telegram-id&gt;",
                      "hy": "Օգտագործում՝ /deluser &lt;անուն կամ telegram-id&gt;"},
    "no_user_match": {
        "en": ("I couldn't find a unique user matching <b>{target}</b>.\n"
               "Use the exact name from /users, or their telegram id."),
        "hy": ("Չգտա <b>{target}</b>-ին համապատասխանող միակ օգտատիրոջ։\n"
               "Օգտվեք /users-ի ճիշտ անունից կամ telegram id-ից։")},
    "last_admin_del": {"en": "I can't remove the last admin.",
                       "hy": "Չեմ կարող հեռացնել վերջին ադմինին։"},
    "user_deleted": {
        "en": ("🗑️ Deleted <b>{name}</b>. Any spot they owned is now "
               "unassigned and their openings/claims are gone."),
        "hy": ("🗑️ <b>{name}</b> ջնջվեց։ Նրա տեղն այժմ առանց տիրոջ է, "
               "իսկ կիսումներն ու զբաղեցումները հեռացվեցին։")},
    "usage_makeadmin": {"en": "Usage: /makeadmin &lt;name or telegram-id&gt;",
                        "hy": "Օգտագործում՝ /makeadmin &lt;անուն կամ telegram-id&gt;"},
    "already_admin": {"en": "<b>{name}</b> is already an admin.",
                      "hy": "<b>{name}</b>-ն արդեն ադմին է։"},
    "now_admin": {
        "en": ("✅ <b>{name}</b> is now an admin. They get approval "
               "requests and the admin commands."),
        "hy": ("✅ <b>{name}</b>-ն այժմ ադմին է։ Նա կստանա հաստատման հարցումներ "
               "և ադմինի հրամաններ։")},
    "usage_demote": {"en": "Usage: /demote &lt;name or telegram-id&gt;",
                     "hy": "Օգտագործում՝ /demote &lt;անուն կամ telegram-id&gt;"},
    "not_admin": {"en": "<b>{name}</b> is not an admin.",
                  "hy": "<b>{name}</b>-ը ադմին չէ։"},
    "last_admin_dem": {"en": "I can't demote the last admin.",
                       "hy": "Չեմ կարող հեռացնել վերջին ադմինի իրավունքը։"},
    "demoted": {"en": "✅ <b>{name}</b> is no longer an admin.",
                "hy": "✅ <b>{name}</b>-ն այլևս ադմին չէ։"},
    "users_title": {"en": "<b>Registered users</b>", "hy": "<b>Գրանցված օգտատերեր</b>"},
    "users_none": {"en": "<i>none yet</i>", "hy": "<i>դեռ ոչ ոք</i>"},
    "users_waiting": {"en": " — <i>waiting to join</i>", "hy": " — <i>սպասում է միանալու</i>"},
    "pending_title": {
        "en": ("<b>Pending approval</b> ({n}) — buttons below, "
               "or use /approve &lt;tg-id&gt; / /reject &lt;tg-id&gt;"),
        "hy": ("<b>Սպասող հաստատումներ</b> ({n}) — կոճակները ներքևում, "
               "կամ օգտվեք /approve &lt;tg-id&gt; / /reject &lt;tg-id&gt; հրամաններից։")},
    "req_title": {"en": "🔔 <b>Registration request</b>",
                  "hy": "🔔 <b>Գրանցման հայտ</b>"},
    "req_body": {"en": "Name: <b>{name}</b>\nTelegram id: <code>{tg}</code>{username}\n\nApprove to let them into the bot.",
                 "hy": "Անուն՝ <b>{name}</b>\nTelegram id՝ <code>{tg}</code>{username}\n\nՀաստատեք, որ մուտք գործեն բոտ։"},
    "usage_approve": {"en": "Usage: /approve &lt;telegram-id&gt;",
                      "hy": "Օգտագործում՝ /approve &lt;telegram-id&gt;"},
    "usage_reject": {"en": "Usage: /reject &lt;telegram-id&gt;",
                     "hy": "Օգտագործում՝ /reject &lt;telegram-id&gt;"},
    "no_pending": {"en": "No pending request for that id.",
                   "hy": "Այդ id-ով սպասող հայտ չկա։"},
    "req_gone": {"en": "That request no longer exists.",
                 "hy": "Այդ հայտն այլևս չկա։"},
    "req_handled": {"en": "That request was already handled.",
                    "hy": "Այդ հայտն արդեն մշակվել է։"},
    "approve_conflict": {
        "en": ("⚠️ Couldn't approve <b>{name}</b> — that name or Telegram "
               "account is already used by another user. Use /rename to free "
               "the name, or ask them for a different one."),
        "hy": ("⚠️ Չհաջողվեց հաստատել <b>{name}</b>-ին — այդ անունը կամ Telegram "
               "հաշիվն արդեն օգտվում է մեկ ուրիշը։ Անունն ազատելու համար օգտվեք "
               "/rename-ից կամ խնդրեք այլ անուն։")},
    "approved": {"en": "✅ Approved <b>{name}</b>.", "hy": "✅ <b>{name}</b>-ը հաստատվեց։"},
    "rejected": {"en": "⛔ Rejected <b>{name}</b>.", "hy": "⛔ <b>{name}</b>-ը մերժվեց։"},
    "spots_title": {"en": "<b>Spots</b> ({day})", "hy": "<b>Տեղեր</b> ({day})"},
    "spot_open_by": {"en": "🔓 open (by {who})", "hy": "🔓 բաց է ({who}-ի կողմից)"},
    "spot_taken_by": {"en": "🚗 taken by {who}", "hy": "🚗 զբաղված է՝ {who}"},
    "spot_owner": {"en": "🔒 with owner", "hy": "🔒 տիրոջ մոտ"},
    "spot_free": {"en": "⚪ unassigned", "hy": "⚪ առանց տիրոջ"},
    "usage_assign": {"en": "Usage: /assign &lt;spot#&gt; &lt;name or telegram-id&gt;",
                     "hy": "Օգտագործում՝ /assign &lt;տեղ#&gt; &lt;անուն կամ telegram-id&gt;"},
    "spot_num": {"en": "The spot number must be a number.",
                 "hy": "Տեղի համարը պետք է թիվ լինի։"},
    "no_spot_n": {"en": "There is no spot #{n}.", "hy": "#{n} տեղ չկա։"},
    "owns_other": {"en": "{name} already owns spot <b>#{n}</b>. Unassign it first.",
                   "hy": "{name}-ն արդեն ունի <b>#{n}</b> տեղը։ Նախ ազատեք այն։"},
    "assigned": {"en": "✅ Spot <b>#{n}</b> is now assigned to <b>{name}</b>.{note}",
                 "hy": "✅ <b>#{n}</b> տեղն այժմ հատկացված է <b>{name}</b>-ին։{note}"},
    "cycle_note": {
        "en": ("\n\n⚠️ A rotation cycle is active, so it overrides manual owners "
               "today. Use /addcycles or /clearcycles."),
        "hy": ("\n\n⚠️ Հերթափոխն ակտիվ է, այնպես որ այսօր այն գերազանցում է ձեռքով "
               "նշանակումները։ Օգտվեք /addcycles կամ /clearcycles հրամաններից։")},
    "cycle_note_un": {
        "en": ("\n\n⚠️ A rotation cycle is active, so it overrides manual owners "
               "today. The change takes visible effect once no cycle covers the day."),
        "hy": ("\n\n⚠️ Հերթափոխն ակտիվ է, այնպես որ այսօր այն գերազանցում է ձեռքով "
               "նշանակումները։ Փոփոխությունը կերևա, երբ օրը հերթափոխի մեջ չլինի։")},
    "usage_rename": {"en": "Usage: /rename &lt;name or telegram-id&gt; &lt;new name&gt;",
                     "hy": "Օգտագործում՝ /rename &lt;անուն կամ telegram-id&gt; &lt;նոր անուն&gt;"},
    "new_name_len": {"en": "The new name must be between 1 and 40 characters.",
                     "hy": "Նոր անունը պետք է լինի 1–40 նիշանոց։"},
    "name_used": {"en": "Another user is already named <b>{name}</b>. Names must be unique.",
                  "hy": "<b>{name}</b> անունով այլ օգտատեր արդեն կա։ Անունները պետք է եզակի լինեն։"},
    "renamed": {"en": "✏️ User renamed to <b>{name}</b>.",
                "hy": "✏️ Օգտատերը վերանվանվեց՝ <b>{name}</b>։"},
    "usage_unassign": {"en": "Usage: /unassign &lt;spot# or name&gt;",
                       "hy": "Օգտագործում՝ /unassign &lt;տեղ# կամ անուն&gt;"},
    "no_spot_user": {"en": "There is no spot <b>#{target}</b> and no user matching <b>{target}</b>.",
                     "hy": "Չկա <b>#{target}</b> տեղ և <b>{target}</b>-ին համապատասխանող օգտատեր։"},
    "owns_nothing": {"en": "<b>{name}</b> doesn't own a spot.",
                     "hy": "<b>{name}</b>-ը տեղ չունի։"},
    "unassigned": {"en": "⚪ Spot <b>#{n}</b> is now unassigned.{note}",
                   "hy": "⚪ <b>#{n}</b> տեղն այժմ առանց տիրոջ է։{note}"},
    "usage_settype": {"en": "Usage: /settype &lt;spot#&gt; reserved|rotating",
                      "hy": "Օգտագործում՝ /settype &lt;տեղ#&gt; reserved|rotating"},
    "settype_ok": {"en": "✅ Spot <b>#{n}</b> is now <b>{type}</b>.",
                   "hy": "✅ <b>#{n}</b> տեղն այժմ <b>{type}</b> է։"},
    "resetclaims": {"en": "🧹 Cleared {n} active claim(s) for today.",
                    "hy": "🧹 Այսօրվա {n} ակտիվ զբաղեցում մաքրվեց։"},
    "cycle_none": {"en": "No rotation cycles yet. Add a plan with /addcycles.",
                   "hy": "Հերթափոխներ դեռ չկան։ Ավելացրեք պլան /addcycles-ով։"},
    "cycle_title": {"en": "🔄 <b>Rotation cycles</b>", "hy": "🔄 <b>Հերթափոխներ</b>"},
    "cycle_current": {"en": "▶️ <b>Current cycle</b> — until <b>{until}</b>",
                      "hy": "▶️ <b>Ընթացիկ հերթափոխ</b> — մինչև <b>{until}</b>"},
    "cycle_idle": {"en": "<i>No cycle is active today.</i>",
                   "hy": "<i>Այսօր ակտիվ հերթափոխ չկա։</i>"},
    "cycle_all": {"en": "<b>All cycles</b>", "hy": "<b>Բոլոր հերթափոխները</b>"},
    "addcycles_prompt": {
        "en": ("Send the rotation plan as text. One block per cycle:\n\n"
               "<pre>Cycle 1 12/10/26-31/12/26\n"
               "1 - Test\n"
               "2 - Test2\n"
               "Cycle 2 01/01/27-31/03/27\n"
               "1 - test3\n"
               "2 - test2</pre>\n\n"
               "Dates are day-first (<b>DD/MM/YY</b>). Names that aren't known yet are "
               "created automatically. One user owns one spot: a name may appear only "
               "once per cycle, and while a cycle is active, spots you don't list "
               "count as unassigned (manual owners return when no cycle is active).\n"
               "Send /cancel to abort."),
        "hy": ("Ուղարկեք հերթափոխի պլանը տեքստով։ Յուրաքանչյուր հերթափոխը՝ առանձին բլոկ.\n\n"
               "<pre>Cycle 1 12/10/26-31/12/26\n"
               "1 - Անուն\n"
               "2 - Անուն2</pre>\n\n"
               "Ամսաթվերը՝ օրն առաջ (<b>DD/MM/YY</b>)։ Անծանոթ անունները ստեղծվում են "
               "ավտոմատ։ Մեկ օգտատեր՝ մեկ տեղ. անունը կարող է հանդիպել միայն մեկ անգամ "
               "մեկ հերթափոխում, իսկ ակտիվ հերթափոխի դեպքում չնշված տեղերը համարվում են "
               "առանց տիրոջ (ձեռքով նշանակումները վերադառնում են, երբ օրը հերթափոխի "
               "մեջ չէ)։\n"
               "Չեղարկելու համար ուղարկեք /cancel։"),
    },
    "cycles_cancelled": {"en": "Cancelled the cycle entry.",
                         "hy": "Հերթափոխի մուտքագրումը չեղարկվեց։"},
    "cycles_no_exist": {"en": "There is no spot <b>#{n}</b>. Nothing was saved — fix it and send again, or /cancel.",
                        "hy": "#{n} տեղ չկա։ Ոչինչ չպահպանվեց — ուղղեք և նորից ուղարկեք, կամ /cancel։"},
    "cycles_dup_spot": {
        "en": ("⚠️ Spot <b>#{n}</b> is listed twice in <b>{label}</b>. Nothing was saved — "
               "fix it and send again, or /cancel."),
        "hy": ("⚠️ <b>#{n}</b> տեղը երկու անգամ է նշված <b>{label}</b>-ում։ Ոչինչ չպահպանվեց — "
               "ուղղեք և նորից ուղարկեք, կամ /cancel։")},
    "cycles_dup_user": {
        "en": ("⚠️ <b>{name}</b> is listed twice in <b>{label}</b> — one user can own "
               "one spot. Nothing was saved — fix it and send again, or /cancel."),
        "hy": ("⚠️ <b>{name}</b>-ը երկու անգամ է նշված <b>{label}</b>-ում — մեկ օգտատերը "
               "կարող է ունենալ մեկ տեղ։ Ոչինչ չպահպանվեց — ուղղեք և նորից ուղարկեք, "
               "կամ /cancel։")},
    "cycles_save_fail": {"en": "⚠️ {err} Nothing was saved — fix it and send again, or /cancel.",
                         "hy": "⚠️ {err} Ոչինչ չպահպանվեց — ուղղեք և նորից ուղարկեք, կամ /cancel։"},
    "cycles_added": {"en": "✅ Added <b>{n}</b> cycle(s):",
                     "hy": "✅ Ավելացվեց <b>{n}</b> հերթափոխ։"},
    "cycles_created": {"en": "👤 Created new (pending) users: {names}",
                       "hy": "👤 Ստեղծվեցին նոր (սպասող) օգտատերեր՝ {names}"},
    "cycles_live": {"en": "▶️ The cycle active today now ends on <b>{until}</b>.",
                    "hy": "▶️ Այսօր ակտիվ հերթափոխն ավարտվում է <b>{until}</b>։"},
    "usage_delcycle": {"en": "Usage: /delcycle &lt;id&gt;  (see ids in /cycle)",
                       "hy": "Օգտագործում՝ /delcycle &lt;id&gt; (id-ները՝ /cycle-ում)"},
    "no_cycle": {"en": "There is no cycle with id {id}.",
                 "hy": "{id} id-ով հերթափոխ չկա։"},
    "cycle_deleted": {"en": "🗑️ Deleted cycle {id}.", "hy": "🗑️ {id} հերթափոխը ջնջվեց։"},
    "cycles_cleared": {"en": "🧹 Removed {n} cycle(s). Spots fall back to their manual owners.",
                       "hy": "🧹 {n} հերթափոխ հեռացվեց։ Տեղերը վերադառնում են ձեռքով նշանակված տերերին։"},
    "parse_fix": {"en": "⚠️ {err}\n\nFix it and send again, or /cancel.",
                  "hy": "⚠️ {err}\n\nՈւղղեք և նորից ուղարկեք, կամ /cancel։"},
}


def t(lang: str, key: str, **kwargs) -> str:
    """Render string ``key`` in ``lang`` (English fallback)."""
    entry = STRINGS.get(key)
    if entry is None:
        return key
    template = entry.get(lang) or entry.get("en") or key
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError):
            return template
    return template


def month_name(month: int, lang: str) -> str:
    names = MONTHS.get(lang) or MONTHS["en"]
    return names[month - 1]


def month_abbr(month: int, lang: str) -> str:
    names = MONTHS_ABBR.get(lang) or MONTHS_ABBR["en"]
    return names[month - 1]


def weekdays(lang: str) -> list:
    return list(WEEKDAYS.get(lang) or WEEKDAYS["en"])


def pretty_day(iso: str, lang: str) -> str:
    """Short human date: 'Mon 12 Oct' in English, '12.10 (Եկ)' in Armenian."""
    from datetime import date as _date

    d = _date.fromisoformat(iso)
    if lang == "hy":
        return f"{d.day:02d}.{d.month:02d} ({WEEKDAYS['hy'][d.weekday()]})"
    return d.strftime("%a %d %b")
