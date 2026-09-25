from app.agent.state import ApprovalRequest


class ApprovalManager:

    def create_request(
        self,
        tool_name: str,
        arguments: dict,
        risk: str,
    ) -> ApprovalRequest:

        if risk == "destructive":
            reason = (
                f"The tool '{tool_name}' performs a "
                "potentially destructive operation."
            )
        else:
            reason = (
                f"The tool '{tool_name}' modifies the "
                "repository."
            )

        return ApprovalRequest(
            tool_name=tool_name,
            arguments=arguments,
            risk=risk,
            reason=reason,
        )

    def approve(
        self,
        approval: ApprovalRequest,
    ) -> ApprovalRequest:

        approval.status = "approved"

        return approval

    def reject(
        self,
        approval: ApprovalRequest,
    ) -> ApprovalRequest:

        approval.status = "rejected"

        return approval