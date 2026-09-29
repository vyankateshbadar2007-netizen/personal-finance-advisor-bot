# Deployment & Verification Checklist — Personal Finance Advisor Bot

## Pre-requisites
- [ ] Python 3.8+ installed
- [ ] `pip install -r requirements.txt` completes
- [ ] `.env` created
- [ ] Git repository configured
- [ ] `.env` is ignored by Git

## Gemini
- [ ] Gemini API key configured
- [ ] GEMINI_MODEL points to a supported model
- [ ] `/api/health` reports Gemini configured when expected
- [ ] AI analysis returns structured JSON

## Core workflow
- [ ] Income validation works
- [ ] At least one expense is required
- [ ] Goal selection works
- [ ] Daily expense log works
- [ ] Weekly expense log works
- [ ] Monthly expense log works
- [ ] Budget cards render
- [ ] Spending analysis renders
- [ ] Saving suggestions render
- [ ] Monthly summary renders
- [ ] Results smooth-scroll into view

## Persistence
- [ ] SQLite database file is created
- [ ] AnalysisReport rows are created
- [ ] ExpenseEntry rows are created
- [ ] LocalStorage history persists after reload
- [ ] Delete history works
- [ ] Clear history works

## Google Sheets
- [ ] Apps Script webhook configured
- [ ] Sync succeeds when configured
- [ ] App still works when Sheets is unavailable

## Deployment
- [ ] `python app.py` works locally
- [ ] `python run_public.py` opens an Ngrok tunnel
- [ ] Public URL loads
- [ ] API requests work through the public URL
- [ ] No API key is committed to Git

## UI/UX
- [ ] Desktop layout works
- [ ] Tablet layout works
- [ ] Mobile layout works
- [ ] Navigation works
- [ ] Forms are accessible
- [ ] Loading state works
- [ ] Toast notifications work
- [ ] No horizontal scroll on mobile

## Final acceptance
- [ ] Scenario 1 tested
- [ ] Scenario 2 tested
- [ ] Scenario 3 tested
- [ ] Scenario 4 tested
- [ ] README is updated
- [ ] SkillWallet links are ready for submission
