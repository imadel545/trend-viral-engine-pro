#!/bin/bash
###############################################################################
# Script de Démarrage Complet - Trend & Viral Engine Pro
# 
# Lance automatiquement :
# - Backend FastAPI (port 8000)
# - Frontend Next.js (port 3000)
#
# Usage: ./start_fullstack.sh
###############################################################################

set -e  # Exit on error

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ASCII Art
echo -e "${MAGENTA}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════════╗
║         TREND & VIRAL ENGINE PRO - FULLSTACK STARTUP            ║
╚══════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Fonction pour tuer les processus au exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Arrêt des serveurs...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✅ Serveurs arrêtés${NC}"
    exit 0
}

trap cleanup EXIT INT TERM

# Vérifications préliminaires
echo -e "${CYAN}🔍 Vérification de l'environnement...${NC}"

# 1. Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 non trouvé${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 installé${NC}"

# 2. Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js non trouvé${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js installé${NC}"

# 3. Virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚙️  Création du venv Python...${NC}"
    python3 -m venv venv
fi

# 4. Backend dependencies
echo -e "${CYAN}📦 Installation des dépendances backend...${NC}"
source venv/bin/activate
pip install -q -r requirements-fixed.txt
echo -e "${GREEN}✓ Dépendances backend OK${NC}"

# 5. Frontend dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${CYAN}📦 Installation des dépendances frontend...${NC}"
    cd frontend
    npm install --silent
    cd ..
    echo -e "${GREEN}✓ Dépendances frontend OK${NC}"
else
    echo -e "${GREEN}✓ Dépendances frontend déjà installées${NC}"
fi

# Création des répertoires nécessaires
echo -e "${CYAN}📁 Création des répertoires...${NC}"
mkdir -p data/raw data/features data/labels data/predictions data/feedback
mkdir -p logs models outputs
echo -e "${GREEN}✓ Répertoires créés${NC}"

echo ""
echo -e "${MAGENTA}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🚀 LANCEMENT DES SERVEURS${NC}"
echo -e "${MAGENTA}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Démarrage du BACKEND
echo -e "${BLUE}⚙️  [BACKEND] Démarrage FastAPI sur http://localhost:8000${NC}"
source venv/bin/activate
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 &
BACKEND_PID=$!

# Attendre que le backend soit prêt
echo -e "${YELLOW}⏳ Attente du backend...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend démarré (PID: $BACKEND_PID)${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Timeout backend${NC}"
        cat logs/backend.log
        exit 1
    fi
done

# Démarrage du FRONTEND
echo -e "${BLUE}⚙️  [FRONTEND] Démarrage Next.js sur http://localhost:3000${NC}"
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Attendre que le frontend soit prêt
echo -e "${YELLOW}⏳ Attente du frontend...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend démarré (PID: $FRONTEND_PID)${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Timeout frontend${NC}"
        cat logs/frontend.log
        exit 1
    fi
done

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ SERVEURS DÉMARRÉS AVEC SUCCÈS !${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}📍 URLs disponibles :${NC}"
echo -e "   ${BLUE}🖥️  Frontend:${NC}       http://localhost:3000"
echo -e "   ${BLUE}🔌 Backend API:${NC}     http://localhost:8000"
echo -e "   ${BLUE}📚 API Docs:${NC}        http://localhost:8000/docs"
echo -e "   ${BLUE}❤️  Health Check:${NC}   http://localhost:8000/health"
echo ""
echo -e "${YELLOW}📝 Logs :${NC}"
echo -e "   Backend:  ${CYAN}tail -f logs/backend.log${NC}"
echo -e "   Frontend: ${CYAN}tail -f logs/frontend.log${NC}"
echo ""
echo -e "${MAGENTA}════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}⚡ Appuyez sur Ctrl+C pour arrêter tous les serveurs${NC}"
echo -e "${MAGENTA}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Garder le script actif
wait
