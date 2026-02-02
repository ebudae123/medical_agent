async function startConversation() {
    try {
        // First, check if patient has an existing active/escalated conversation
        const checkResponse = await fetch(`${API_BASE}/conversations/patient/${currentUser.user_id}/latest`);
        const checkData = await checkResponse.json();

        if (checkData.exists) {
            // Load existing conversation
            currentConversation = checkData;

            // Load all existing messages
            const messagesResponse = await fetch(`${API_BASE}/conversations/${currentConversation.id}`);
            const conversationData = await messagesResponse.json();

            // Display all existing messages
            conversationData.messages.forEach(msg => {
                const senderType = msg.sender_type.toLowerCase();
                addMessage(senderType, msg.content, msg.risk_level);
                lastMessageCount++;
            });
        } else {
            // Create new conversation
            const response = await fetch(`${API_BASE}/conversations`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ patient_id: currentUser.user_id })
            });

            currentConversation = await response.json();
        }

        // Start polling for new messages (clinician responses)
        startMessagePolling();
    } catch (error) {
        console.error('Error starting conversation:', error);
    }
}
