function Review-PullRequest {
    param($PRData, $ProjectState)
    
    Write-Host "Ghost AI Reviewer: Analyzing PR #$($PRData.id)..." -ForegroundColor Cyan
    
    # Simulate scanning for ticket IDs in title or description
    $match = $null
    foreach ($ticket in $ProjectState.tickets) {
        if ($PRData.title -like "*$($ticket.id)*" -or $PRData.title -like "*$($ticket.title)*") {
            $match = $ticket
            break
        }
    }

    if ($match) {
        $comment = "Ghost Bot Review: This PR successfully addresses $($match.id) ('$($match.title)'). Board status remains synced."
        return @{ success = $true; comment = $comment; ticket_id = $match.id }
    } else {
        $comment = "Ghost Bot Review: Warning! This PR does not clearly map to an open ticket. Please link a Jira/Linear ID to ensure project tracking."
        return @{ success = $false; comment = $comment; ticket_id = $null }
    }
}
