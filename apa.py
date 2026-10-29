import streamlit as st
import pandas as pd

st.title("Last Update Monitoring")

st.divider()

SHEET1_ID = "13q8avPIV2RjBg1tIUeJsd6U23wfOAann30S-d6moQ84" # sosmed fanpagekarma
SHEET2_ID = "1NQgDn4nylze5FqE7LiPbiW7de9F9BITx8T3FveX1Azc" # data windsor
SHEET3_ID = "1Qbk7PfJQhnRi8iMfE-tKzVfA8Uec2vYkLtSQHsjupvE" # data dealer

SHEET1_NAME = "All Content"
SHEET2_NAME = "Master Data Ads"
SHEET3_NAME = "Online Leads"

@st.cache_data(ttl=60)
def load_data(sheet_id, sheet_name):
    
    encoded_name = sheet_name.replace(" ", "%20") 
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_name}"
    callbackURL = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()

    st.caption(f"Menampilkan: {callbackURL}")
    return df

# =================== read data sosmed fanpagekarma
try:
    df1 = load_data(SHEET1_ID, SHEET1_NAME)
except Exception as e:
    st.error(f"❌ Gagal load data: {e}")
    st.stop()

# =================== read data windsor
try:
    df2 = load_data(SHEET2_ID, SHEET2_NAME)
except Exception as e:
    st.error(f"❌ Gagal load data: {e}")
    st.stop()

#read data dealer
try:
    df3 = load_data(SHEET3_ID, SHEET3_NAME)
except Exception as e:
    st.error(f"❌ Gagal load data: {e}")
    st.stop()

st.divider()

# ==========================
# Data Sosmed Fanpagekarma
# ==========================

if "id" not in df1.columns:
    st.warning(f"⚠️ Kolom 'id' tidak ditemukan.")
    st.write("Kolom tersedia:", df1.columns.tolist())
    st.stop()

# ── Tambah kolom checker ──────────────────────────────────────────────────────
df1["checker"] = df1.duplicated(subset=["id"], keep=False).map({True: "Duplicate", False: "Unique"})

# ── Latest Update per Platform ────────────────────────────────────────────────
st.markdown("### 🕐 Latest Update per Platform")

required_cols = ["Date", "link", "Platform", "image"]

if all(c in df1.columns for c in required_cols):
    df1["Date"] = pd.to_datetime(df1["Date"], errors="coerce")

    summary_content_rows = []
    summary_followers_rows = []
    summary_daily_account_rows = []

    for plat in sorted(df1["Platform"].dropna().unique()):
        df_plat = df1[df1["Platform"] == plat].copy()

        # Helper mask
        # ==========================
        image_filled = (
            df_plat["image"].notna()
            & (df_plat["image"].astype(str).str.strip() != "")
        )

        image_empty = (
            df_plat["image"].isna()
            | (df_plat["image"].astype(str).str.strip() == "")
        )

        account_filled = (
            df_plat["account_impression"].notna()
            & (df_plat["account_impression"].astype(str).str.strip() != "")
        )

        account_empty = (
            df_plat["account_impression"].isna()
            | (df_plat["account_impression"].astype(str).str.strip() == "")
        )

        # Klasifikasi data
        # ==========================
        # Content -> image ada
        df_content = df_plat[image_filled]

        # Followers -> image kosong & account_impression kosong
        df_followers = df_plat[image_empty & account_empty]

        df_followers["Growth"] = pd.to_numeric(
            df_followers["Growth"],
            errors="coerce"
        )

        # Daily Account -> image kosong & account_impression terisi
        df_daily_account = df_plat[image_empty & account_filled]

        df_daily_account["account_impression"] = pd.to_numeric(
            df_daily_account["account_impression"],
            errors="coerce"
        )

        # Field Rule
        # ==========================
        # Checker
        if "checker" in df_content.columns and not df_content["checker"].dropna().empty:
            content_field_rule = (
                "Duplicate"
                if (df_content["checker"] == "Duplicate").any()
                else "Unique"
            )
        else:
            content_field_rule = "-"

        # Latest Followers
        if not df_followers.empty and not df_followers["Date"].dropna().empty:
            idx = df_followers["Date"].idxmax()
            followers_field_rule = df_followers.loc[idx, "Followers"]   # atau "Followers"
        else:
            followers_field_rule = "-"

        # Latest Daily Account Impression
        if not df_daily_account.empty and not df_daily_account["Date"].dropna().empty:
            idx = df_daily_account["Date"].idxmax()
            daily_account_field_rule = df_daily_account.loc[idx, "account_impression"]
        else:
            daily_account_field_rule = "-"

        # Summary - Content
        # ==========================
        if not df_content.empty:
            latest_row = df_content.loc[df_content["Date"].idxmax()]

            summary_content_rows.append({
                "Platform": f"{plat} Content",
                "Last Update": (
                    latest_row["Date"]
                    if pd.notna(latest_row["Date"])
                    else "-"
                ),
                "Link": latest_row["link"],
                "Checker": content_field_rule,
                "Latest Followers": "-",
                "Latest Accounts": "-"
            })

        # Summary - Followers
        # ==========================
        if not df_followers.empty:
            latest_row = df_followers.loc[df_followers["Date"].idxmax()]

            summary_followers_rows.append({
                "Platform": f"{plat} Followers",
                "Last Update": (
                    latest_row["Date"]
                    if pd.notna(latest_row["Date"])
                    else "-"
                ),
                "Link": latest_row["link"],
                "Checker": "-",
                "Latest Followers": followers_field_rule,
                "Latest Accounts": "-"
            })

        # Summary - Daily Account
        # ==========================
        if not df_daily_account.empty:
            latest_row = df_daily_account.loc[
                df_daily_account["Date"].idxmax()
            ]

            summary_daily_account_rows.append({
                "Platform": f"{plat} Daily Account",
                "Last Update": (
                    latest_row["Date"]
                    if pd.notna(latest_row["Date"])
                    else "-"
                ),
                "Link": latest_row["link"],
                "Checker": "-",
                "Latest Followers": "-",
                "Latest Accounts": daily_account_field_rule
            })

    # Final Summary Table
    # ==========================
    latest_per_platform = pd.DataFrame(
        summary_content_rows
        + summary_followers_rows
        + summary_daily_account_rows
    )

    st.dataframe(
        latest_per_platform,
        use_container_width=True,
        hide_index=True
    )

else:
    missing = [c for c in required_cols if c not in df1.columns]
    st.warning(f"⚠️ Kolom tidak ditemukan: {missing}")

st.divider()

# ==========================
# Data Windsor
# ==========================

st.markdown("### 🕐 Latest Update per Publisher Platform")
 
required_cols_2 = ["Date", "Publisher Platform"]
 
if all(c in df2.columns for c in required_cols_2):
    df2["Date"] = pd.to_datetime(df2["Date"], errors="coerce")
 
    summary_windsor_rows = []
 
    for pub_plat in sorted(df2["Publisher Platform"].dropna().unique()):
        df_pub = df2[df2["Publisher Platform"] == pub_plat].copy()
 
        if df_pub["Date"].dropna().empty:
            continue
 
        latest_row = df_pub.iloc[-1]
 
        # Checker
        checker_val = (
            "Duplicate" if (df_pub["checker"] == "Duplicate").any() else "Unique"
        ) if "checker" in df_pub.columns else "-"
 
        # Link (opsional, jika ada)
        if "Media URL" not in df_pub.columns or pub_plat == "google":
            link_val = latest_row["Landing Page"] if "Landing Page" in df_pub.columns and pd.notna(latest_row["Landing Page"]) else "-"
        else:
            link_val = latest_row["Media URL"] if pd.notna(latest_row["Media URL"]) else "-"
 
        # Spend (opsional, jika ada)
        spend_val = "-"
        spend_col = next((c for c in ["Spend", "spend", "Amount Spent"] if c in df_pub.columns), None)
        if spend_col:
            latest_spend = pd.to_numeric(df_pub.iloc[-1][spend_col], errors="coerce")  # ganti dari idxmax()
            spend_val = latest_spend if pd.notna(latest_spend) else "-"
 
        summary_windsor_rows.append({
            "Publisher Platform": pub_plat,
            "Last Update": latest_row["Date"] if pd.notna(latest_row["Date"]) else "-",
            "Link": link_val,
            "Latest Spend": spend_val,
        })
 
    latest_windsor = pd.DataFrame(summary_windsor_rows)
    st.dataframe(latest_windsor, use_container_width=True, hide_index=True)
 
else:
    missing = [c for c in required_cols_2 if c not in df2.columns]
    st.warning(f"⚠️ Kolom tidak ditemukan di Sheet2: {missing}")
    st.write("Kolom tersedia:", df2.columns.tolist())
 
st.divider()

# ==========================
# SECTION 3: Data Dealer
# Grouping by: dealer_name
# ==========================
 
st.markdown("## 🏬 Dealer (Online Leads)")
 
st.markdown("### 🕐 Latest Update per Dealer")
 
required_cols_3 = ["create_time", "dealer_name"]
 
if all(c in df3.columns for c in required_cols_3):
    df3["create_time"] = pd.to_datetime(df3["create_time"], errors="coerce")
 
    # Duplicate checker
    id_col_3 = next((c for c in ["email"] if c in df3.columns), None)
    if id_col_3:
        df3["checker"] = df3.duplicated(subset=[id_col_3], keep=False).map({True: "Duplicate", False: "Unique"})
    else:
        df3["checker"] = "Unique"
 
    summary_dealer_rows = []
 
    for dealer in sorted(df3["dealer_name"].dropna().unique()):
        df_dealer = df3[df3["dealer_name"] == dealer].copy()
 
        if df_dealer["create_time"].dropna().empty:
            continue
 
        latest_row = df_dealer.loc[df_dealer["create_time"].idxmax()]
 
        # Checker
        checker_val = (
            "Duplicate" if (df_dealer["checker"] == "Duplicate").any() else "Unique"
        ) if "checker" in df_dealer.columns else "-"

        # nomer HP
        last_phone = latest_row["phone_number"] if "phone_number" in df_dealer.columns else "-"

        # email
        last_email = latest_row["email"] if "email" in df_dealer.columns else "-"

        # nama
        first_name = latest_row["first_name"] if "first_name" in df_dealer.columns else "-"

        # kota
        city = latest_row["city_name"] if "city_name" in df_dealer.columns else "-"

        # model mobil
        model_name = latest_row["model_name"] if "model_name" in df_dealer.columns else "-"

        #remarks
        remarks = latest_row["remarks"] if "remarks" in df_dealer.columns else "-"

        # Total leads (opsional, jumlah baris per dealer)
        total_leads = df_dealer[df_dealer["create_time"] == latest_row["create_time"]]["email"].nunique() if "email" in df_dealer.columns else "-"
 
        summary_dealer_rows.append({
            "Dealer Name": dealer,
            "Last Update": latest_row["create_time"] if pd.notna(latest_row["create_time"]) else "-",
            "Email Source": last_email,
            "Phone Number": last_phone,
            "First Name": first_name,
            "City": city,
            "Model Name": model_name,
            "Remarketing": remarks,
            "Total Leads": total_leads,
        })
 
    latest_dealer = pd.DataFrame(summary_dealer_rows)
    st.dataframe(latest_dealer, use_container_width=True, hide_index=True)
 
else:
    missing = [c for c in required_cols_3 if c not in df3.columns]
    st.warning(f"⚠️ Kolom tidak ditemukan di Sheet3: {missing}")
    st.write("Kolom tersedia:", df3.columns.tolist())