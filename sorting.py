class RadixSortEngine:
    @staticmethod
    def sort(prof_objects, desc=False):
        """Stable LSD radix sort on lowercased Unicode names."""
        if not prof_objects:
            return []
        max_len = max(len(p["name"]) for p in prof_objects)
        items = [(p["name"].casefold().ljust(max_len, "\0"), p)
                 for p in prof_objects]
        for index in range(max_len - 1, -1, -1):
            buckets = {}
            for key, obj in items:
                buckets.setdefault(ord(key[index]), []).append((key, obj))
            items = [item for code in sorted(buckets) for item in buckets[code]]
        result = [obj for _, obj in items]
        return result[::-1] if desc else result


class BinarySearchEngine:
    @staticmethod
    def search(sorted_list, target_name):
        """Find a professor by exact name (case-insensitive)."""
        low, high = 0, len(sorted_list) - 1
        target = target_name.strip().casefold()
        while low <= high:
            mid = (low + high) // 2
            curr = sorted_list[mid]["name"].strip().casefold()
            if curr == target:
                return mid
            if curr < target:
                low = mid + 1
            else:
                high = mid - 1
        return -1

