# The goal is to make sure:
#   1) everyone is in 1 and only 1 group.
#   2) every group has only 1 submission (if more, which we choose is undefined behavior).

import re
NETID_PATTERN = "[a-zA-Z]{3}[0-9]{3,4}"


# Signature: submission -> list of netids or None
# netids must be lower-case
def submission_to_netids_rule(submission):
    if "attachments" not in submission:
        return None
    if len(submission["attachments"]) == 0:
        return None
    attachment = submission["attachments"][0]
    raw_filename = attachment["filename"]
    netids = [s.lower() for s in re.findall(NETID_PATTERN, raw_filename)]
    return netids

# for students that submitted wrong net_ids:
# parse comments, from newest to oldest, until a non-empty list is found:
def submission_to_netids_patch_rule(submission):
    comments = submission["submission_comments"]
    for comment in comments[::-1]:
        netids = [s.lower() for s in re.findall(NETID_PATTERN, comment["comment"])]
        if len(netids) > 0:
            return netids
    return None

class Grouper:
    def __init__(self, student_list, min_member_count, max_member_count):
        self.min_member_count = min_member_count
        self.max_member_count = max_member_count
        # initialize states:
        self._id_to_group = {}
        self._group_to_leader = {} # define a "leader" is who submits
        self._cursor = 0
        self._netid_to_id_map = {}
        for student in student_list:
            netid = student["sis_user_id"]
            student_id = student["id"]
            self._netid_to_id_map[netid] = student_id
            self._id_to_group[student_id] = None
        # collecting errors:
        self._errors = []

    def accept(self, student_id, submission):
        netids = submission_to_netids_rule(submission)
        if netids is None: # the student is not a leader
            return
        members_is_found = False
        try:
            members = [self._netid_to_id_map[n] for n in netids]
            members_is_found = True
        except:
            pass 
        if not members_is_found or len(members) == 0:
            try:
                netids_new = submission_to_netids_patch_rule(submission)
                members = [self._netid_to_id_map[n] for n in netids_new]
            except:
                self._errors.append("%d: invalid netid exists %s & %s" % (student_id, netids, netids_new))
                return
        if len(members) < self.min_member_count:
            self._errors.append("%d: too few members found %s" % (student_id, members))
            return
        if student_id not in members:
            self._errors.append("%d: the student hemself is not a member %s" % (student_id, members))
            return
        if len(members) > self.max_member_count:
            self._errors.append("%d: too many members found %s" % (student_id, members))
            return
        curr_groups = [self._id_to_group[m] for m in members]
        if any(x is not None for x in curr_groups):
            if all(x == curr_groups[0] for x in curr_groups):
                self._errors.append("%d: repetitive submission %s" % (student_id, members))
            else:
                self._errors.append("%d: conflict with other groups %s" % (student_id, members))
            return
        # Success!
        for member in members:
            self._id_to_group[member] = self._cursor
        self._group_to_leader[self._cursor] = student_id
        self._cursor += 1

    def load(self, groups): # load from an old group, and return all un-grouped students
        for i in range(len(groups)):
            group = groups[i]
            self._group_to_leader[i] = group["leader"]
            for member in group["members"]:
                self._id_to_group[member] = i
        self._cursor = len(groups)
        unassigned = []
        for student_id in self._id_to_group:
            group_id = self._id_to_group[student_id]
            if group_id is None:
                unassigned.append(student_id)
        return unassigned
    
    def finalize(self):
        groups = []
        for i in range(self._cursor):
            groups.append({
                "leader": self._group_to_leader[i],
                "members": []
            })
        for student_id in self._id_to_group:
            group_id = self._id_to_group[student_id]
            if group_id is None:
                self._errors.append("%d: not in any group" % student_id)
            else:
                groups[group_id]["members"].append(student_id)
        return groups, self._errors
        
        